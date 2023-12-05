import pandas as pd
import world_bank_data as wbd
import geopandas as gpd


############## IMPORTING DATA FOR DEATH CAUSES, DEATH RATES, POPULATION AND GEOSPATIAL POSITIONS ##############
# https://www.kaggle.com/datasets/ivanchvez/causes-of-death-our-world-in-data
death_causes = pd.read_csv('https://raw.githubusercontent.com/Denze8/Data-Visualization-Project/main/Data/cause_of_deaths.csv?token=GHSAT0AAAAAACHXHC7NOSJWTRNS4IFMBACOZIIEG7A')

#
death_rates = pd.read_csv('https://raw.githubusercontent.com/Denze8/Data-Visualization-Project/main/Data/death_rates.csv')

# https://data.worldbank.org/indicator/SP.POP.TOTL
population = pd.read_csv('https://raw.githubusercontent.com/Denze8/Data-Visualization-Project/main/Data/population.csv?token=GHSAT0AAAAAACHXHC7NUXI5CZJQUGBPI52UZIIEGIQ')

# Using-built in dataset in Geopandas
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

############## DATA PREPROCESSING FOR DEATH CAUSES AND POPULATION ##############
# First subsetting population and death_rates by the years recorded in our dataset with death causes.
years_in_death_causes = [str(year) for year in death_causes.loc[:,'Year'].unique().tolist()]
population = population.rename(columns={'Country Name': 'Country', 'Country Code': 'Code'})
population = population[['Country', 'Code']].join(population[years_in_death_causes])
death_rates = population.rename(columns={'Country Name': 'Country', 'Country Code': 'Code'})
death_rates = death_rates[['Country', 'Code']].join(death_rates[years_in_death_causes])
# Changing some relevant names in death_causes.
death_causes = death_causes.rename(columns={'Country/Territory': 'Country', 'Code': 'Code'})


# Then filtering population and death_rates by countries in our dataset with death causes using their codes.
countries_in_death_causes = [country_code for country_code in death_causes.loc[:,'Code'].unique().tolist()]
population = population[population['Code'].isin(countries_in_death_causes)]
death_rates = death_rates[death_rates['Code'].isin(countries_in_death_causes)]


# Cook Island, Niue & Tokelau is counted as part of New Zealand in our dataset for death_causes.
codes_NZ = ['COK', 'NZL', 'NIU', 'TKL']
NZ = death_causes[death_causes['Code'].isin(codes_NZ)].groupby(by = ['Year'], as_index = False).sum()
NZ['Code'] = 'NZL'
NZ['Country'] = 'New Zealand'

indexes_NZL_death_causes = death_causes[death_causes['Code'] == 'NZL'].index.tolist()
index_NZ = 0
for index in indexes_NZL_death_causes:
    death_causes.loc[index] = NZ.loc[index_NZ]
    index_NZ += 1

# Taiwan is counted as a part of China.
codes_CN = ['CHN', 'TWN']
CN = death_causes[death_causes['Code'].isin(codes_CN)].groupby(by = 'Year', as_index = False).sum()
CN['Code'] = 'CHN'
CN['Country'] = 'China'

indexes_CHN_death_causes = death_causes[death_causes['Code'] == 'CHN'].index.tolist()
index_CN = 0
for index in indexes_CHN_death_causes:
    death_causes.loc[index] = CN.loc[index_CN]
    index_CN += 1

# Remove Cook Island, Niue, Tokelau and Taiwan from our dataset for death causes.
countries_to_stay = [country for country in countries_in_death_causes 
                        if country not in ['COK','NIU','TKL','TWN']]
death_causes = death_causes.loc[(death_causes['Code'].isin(countries_to_stay))].reset_index(drop = True)

# Make our dataset for population and the same format as dataset for death causes.
population = population.melt(id_vars = ['Country', 'Code'], var_name = 'Year', value_name = 'Population').astype({'Year': int})
death_rates = death_rates.melt(id_vars = ['Country', 'Code'], var_name = 'Year', value_name = 'Death Rate').astype({'Year': int})

############## IMPORTING DATA FOR GDP ##############
GDP = pd.DataFrame(wbd.get_series(indicator = 'NY.GDP.MKTP.KD', country = countries_to_stay, date = '1990:2019')).reset_index()

############## COMBINING ALL FOUR DATASETS  #############
# Firstly making all three datasets the same order. Datasets for death causes.
# are already in same order.
population = population.sort_values(by = ['Country', 'Year'], ignore_index = True)
death_rates = death_rates.sort_values(by = ['Country', 'Year'], ignore_index = True)
GDP = GDP.sort_values(by = 'Country', ignore_index = True)

# Now updating the dataset with death causes to take variables from both GDP and population.
death_causes['Population'] = population.loc[:,'Population']
death_causes['Death Rate'] = death_rates.loc[:,'Death Rate']
death_causes['Total Number of Deaths'] = death_causes.loc[:,'Population']  * (death_causes.loc[:,'Death Rate']/1000)
death_causes['GDP'] = GDP.loc[:,'NY.GDP.MKTP.KD']

# Merging dataset with death causes with geospatial data aka world data, also change name of column.
world = world.rename(columns={'iso_a3': 'Code'})
world = world.drop(['pop_est','name','gdp_md_est'], axis = 1)

death_causes = death_causes.merge(world, on = 'Code')

# Add sum for each group 
groups = {'Infectious Diseases': ['Meningitis', 'Malaria', 'Tuberculosis', 'HIV/AIDS', 'Lower Respiratory Infections', 'Diarrheal Diseases', 'Acute Hepatitis'],
          'Neurological and Cognitive Disorders': ["Alzheimer's Disease and Other Dementias", "Parkinson's Disease"],
          'Nutritional and Metabolic Disorders': ['Nutritional Deficiencies', 'Diabetes Mellitus', 'Chronic Kidney Disease'],
          'Mental Health and Substance Abuse': ['Drug Use Disorders', 'Alcohol Use Disorders', 'Self-harm'],
          'Injuries and Accidents': ['Drowning', 'Road Injuries', 'Poisonings', 'Exposure to Forces of Nature', 'Fire, Heat, and Hot Substances'],
          'Maternal and Child Health': ['Neonatal Disorders', 'Maternal Disorders'],
          'Non-communicable Diseases': ['Cardiovascular Diseases', 'Neoplasms', 'Chronic Respiratory Diseases', 'Cirrhosis and Other Chronic Liver Diseases', 'Digestive Diseases'],
          'Violence and Conflict': ['Interpersonal Violence', 'Conflict and Terrorism']
          }

for index_row, row in death_causes.iterrows():
    for name in groups.keys():
        death_causes[name] = death_causes[groups.get(name)].sum(axis = 1)

# Making into GeoDataFrame
death_causes = gpd.GeoDataFrame(death_causes, geometry = "geometry")

# Save dataset
death_causes.to_file('final_dataset.shp', driver = 'GeoJSON')
