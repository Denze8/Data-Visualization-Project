import numpy as np
import pandas as pd
import json
from bokeh.models import ColumnDataSource, GeoJSONDataSource


def get_geodatasource(gdf):    
    return GeoJSONDataSource(geojson = json.dumps(json.loads(gdf.to_json())))


def Merge(dict1, dict2):
    res = {**dict1, **dict2}
    return res

def correlation_matrix_(X):
    X = np.matrix(X)
    n,d  = X.shape 
    corr = np.zeros((d,d)) 
    for i in range(d): 
        for j in range(d): 
            corr[i,j] = np.round(sum([((X[n,i]-np.mean(X[:,i])) * (X[n,j]-np.mean(X[:,j]))) for n in range(n)])/np.sqrt(sum([(X[n,i]-np.mean(X[:,i]))**2 for n in range(n)])*sum([(X[n,j]-np.mean(X[:,j]))**2 for n in range(n)])),2) 
    return corr

def add_vectors(v1, v2):
    return [v1[i] + v2[i] for i in range(v1.__len__())]


# Adds a weight to a value for multiplication purposes. Weight should be between 0 and 1. A weight of 0 will return 1.
def add_weight(value, weight):
    weighted_value = value * weight
    return 1 - weight + weighted_value


def avg_of_middle_line_first_derivatives(data_dict, rel=False):
    first_derivatives = []
    for key in data_dict.keys():
        layer = data_dict[key]
        for i in range(1, layer.__len__()):
            first_derivative = abs(layer[i] - layer[i - 1])
            if rel:
                layer_thickness_start = layer[i - 1]
                layer_thickness_end = layer[i]
                layer_thickness_avg = (layer_thickness_start + layer_thickness_end) / 2
                if layer_thickness_avg > 0:
                    first_derivative /= layer_thickness_avg
                else:
                    first_derivative = 0
            if layer[i] or layer[i - 1] or not rel:
                first_derivatives.append(first_derivative)
    sum_of_first_derivatives = sum(first_derivatives)
    result = sum_of_first_derivatives / first_derivatives.__len__()
    return result / 2


def avg_of_middle_line_second_derivatives(data_dict, rel=False):
    second_derivatives = []
    for key in data_dict.keys():
        layer = data_dict[key]
        for i in range(2, layer.__len__()):
            second_derivative = abs((layer[i] - layer[i - 1]) - (layer[i - 1] - layer[i - 2]))
            if rel:
                if layer[i - 1] > 0:
                    second_derivative /= layer[i - 1]
                else:
                    second_derivative = 0
            second_derivatives.append(second_derivative)
    sum_of_first_derivatives = sum(second_derivatives)
    result = sum_of_first_derivatives / second_derivatives.__len__()
    return result / 2


def write_ranks(ranks, destination_file):
    destination_file.write('category, rank\n')
    destination_file.write('\"%s\", %d\n' % ("Baseline", 0))
    count = 1
    for rank in ranks:
        destination_file.write('\"%s\", %d\n' % (rank, count))
        count += 1


def write_foundation(foundation, start_cols):
    destination_file = open("baseline.csv", 'w', newline='')
    destination_file_writer = csv.writer(destination_file, delimiter=',', quotechar='"')
    header = start_cols[0]
    header.extend(['Name', 'Value'])
    destination_file_writer.writerow(header)
    for i in range(0, len(foundation)):
        row = start_cols[i + 1]
        row.extend(['Baseline', foundation[i]])
        destination_file_writer.writerow(row)

        
def score(data_dict, ranks, weights, foundation):
    if not foundation:
        foundation = [0] * len(data_dict[ranks[0]])
    chart_score = 0
    for rank in ranks:
        chart_score += layer_score(data_dict[rank], foundation, weights)
        foundation = add_vectors(foundation, data_dict[rank])
    return chart_score


def layer_score(layer, foundation, weights):
    bottom_line = foundation
    middle_line = add_vectors(foundation, [x / 2 for x in layer])
    top_line = add_vectors(foundation, layer)

    layer_score_value = 1

    wiggle_value = 0
    if weights['fda']:
        if weights['bottom_line']:
            wiggle_value += wiggle_line(layer, bottom_line, weights) * weights['bottom_line']
        if weights['middle_line']:
            wiggle_value += wiggle_line(layer, middle_line, weights) * weights['middle_line']
        if weights['top_line']:
            wiggle_value += wiggle_line(layer, top_line, weights) * weights['top_line']
        layer_score_value *= add_weight(wiggle_value, weights['fda'])

    bump_value = 0
    if weights['sda']:
        if weights['bottom_line']:
            bump_value += bump_line(layer, bottom_line, weights) * weights['bottom_line']
        if weights['middle_line']:
            bump_value += bump_line(layer, middle_line, weights) * weights['middle_line']
        if weights['top_line']:
            bump_value += bump_line(layer, top_line, weights) * weights['top_line']
        layer_score_value *= add_weight(bump_value, weights['sda'])

    break_value = 0
    if weights['fdr']:
        if weights['bottom_line']:
            break_value += break_line(layer, bottom_line, weights) * weights['bottom_line']
        if weights['middle_line']:
            break_value += break_line(layer, middle_line, weights) * weights['middle_line']
        if weights['top_line']:
            break_value += break_line(layer, top_line, weights) * weights['top_line']
        layer_score_value *= add_weight(break_value, weights['fdr'])

    return layer_score_value


def wiggle_point(line, j):
    return abs(line[j] - line[j - 1])


def wiggle_line(layer, line, weights):
    return sum(
        [(wiggle_point(line, j)
          * ((layer[j] + layer[j - 1]) ** weights['weight_exponent']))
         for j in range(1, len(line))]) / weights['total_sum']


def bump_point(line, j):
    return abs((line[j] - line[j - 1]) - (line[j - 1] - line[j - 2]))


def bump_line(layer, line, weights):
    return sum(
        [(bump_point(line, j)
          * (layer[j - 1] ** weights['weight_exponent']))
         for j in range(2, len(line))]) / weights['total_sum']


def break_point(layer, line, j):
    if (layer[j] + layer[j - 1]) / 2 == 0:
        return 0
    return (wiggle_point(line, j) / ((layer[j] + layer[j - 1]) / 2)) ** 2


def break_line(layer, line, weights):
    return sum(
        [(break_point(layer, line, j)
          * ((layer[j] + layer[j - 1]) ** weights['weight_exponent']))
         for j in range(1, len(line))]) / weights['total_sum']


def calculate_ranks(data_dict, weights, foundation=None):
    ranks = [x for x in data_dict.keys()]
    if not foundation:
        foundation = [0] * data_dict[ranks[0]].__len__()
    #print("%d layers" % len(ranks))
    #print('Initial:\t%f' % score(data_dict, ranks, weights, foundation))

    ranks, foundation = upwards_opt(data_dict, weights, ranks, foundation)
    return ranks, foundation


def upwards_opt(data_dict, weights, ranks, foundation):
    n = len(ranks)
    old_cost = None
    passes = 0
    swaps = 0
    while not old_cost or score(data_dict, ranks, weights, foundation) < old_cost * (1 - weights['min_improvement']):
        old_cost = score(data_dict, ranks, weights, foundation)
        i = 0
        visited = []
        while i < n:
            if visited.__contains__(i):
                #print("Skip layer %d" % i)
                i += 1
                continue
            new_index = find_best_position(i, data_dict, ranks, weights, foundation)
            if new_index != i:
                # Move the layer
                layer = ranks.pop(i)
                ranks.insert(new_index, layer)
                swaps += 1
                current_score = score(data_dict, ranks, weights, foundation)
            if new_index <= i:
                i += 1
            else:
                # Update visited indices accordingly
                for j in range(len(visited)):
                    v = visited[j]
                    if i < v <= new_index:
                        visited[j] -= 1

                # Insert newIndex
                visited.append(new_index)
        passes += 1
    return ranks, foundation


def find_best_position(i, data_dict, ranks, weights, foundation):
    g_below = foundation
    g_above = add_vectors(foundation, data_dict[ranks[i]])
    cost_below = []
    cost_above = []
    cost_layer = []
    for j in range(len(ranks)):
        if j != i:
            cost_below.append(layer_score(data_dict[ranks[j]], g_below, weights))
            cost_above.append(layer_score(data_dict[ranks[j]], g_above, weights))
            cost_layer.append(layer_score(data_dict[ranks[i]], g_below, weights))
            g_below = add_vectors(g_below, data_dict[ranks[j]])
            g_above = add_vectors(g_above, data_dict[ranks[j]])
    cost_layer.append(layer_score(data_dict[ranks[i]], g_below, weights))

    current_cost = sum(cost_above) + cost_layer[0]
    best_index = 0
    best_cost = current_cost
    for j in range(1, len(ranks)):
        current_cost += cost_below[j - 1] - cost_above[j - 1]
        current_cost += cost_layer[j] - cost_layer[j - 1]
        if current_cost < best_cost:
            best_index = j
            best_cost = current_cost
    return best_index

def abba(data, cause):
    data = pd.DataFrame(data).groupby('Year')[cause].sum().reset_index()
    data_dict = {i : list(data[i])  for i in cause}

    # Settings
    min_improvement = 0.01

    flatness = 0
    straightness = 1
    continuity = 0

    bottom_line = 1
    middle_line = 0
    top_line = 1

    significance = 1

    # ??
    silhouette = None
    for value in data_dict.values():
        #print(value)
        if not silhouette:
            silhouette = value
        else:
            silhouette = add_vectors(silhouette, value)
    # sum
    total_sum = sum([sum([x ** significance for x in layer]) for layer in data_dict.values()])

    weights = {
        'min_improvement': 0.01,
        'fda': 0,
        'sda': 1,
        'fdr': 0,
        'bottom_line': 1,
        'middle_line': 0,
        'top_line': 1,
        'weight_exponent': 1,
        'total_sum': total_sum,
        'silhouette': silhouette,
    }

    line_weight_sum = weights['bottom_line'] + weights['middle_line'] + weights['top_line']
    weights['bottom_line'] /= line_weight_sum
    weights['middle_line'] /= line_weight_sum
    weights['top_line'] /= line_weight_sum

    silhouette_max = max(silhouette)
    ranks, foundation = calculate_ranks(data_dict, weights)
    foundation_min = min(foundation)
    foundation = [x - foundation_min + silhouette_max * 0.05 for x in foundation]

    return ranks