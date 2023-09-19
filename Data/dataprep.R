library(data.table)
library(tidyverse)
library(WDI)

# Import data
# https://www.kaggle.com/datasets/ivanchvez/causes-of-death-our-world-in-data
death     = read.csv("https://raw.githubusercontent.com/Denze8/Data-Visualization-Project/main/Data/cause_of_deaths.csv?token=GHSAT0AAAAAACHXHC7NOSJWTRNS4IFMBACOZIIEG7A")

# https://data.worldbank.org/indicator/SP.POP.TOTL
total_pop = read.csv("https://raw.githubusercontent.com/Denze8/Data-Visualization-Project/main/Data/population.csv?token=GHSAT0AAAAAACHXHC7NUXI5CZJQUGBPI52UZIIEGIQ")

# Years in original data
name = paste(unique(death$Year))

# Filter pop-data on correct years
colnames(total_pop) = gsub("X", "", names(total_pop), fixed = TRUE) 
total_pop           = total_pop[, c(1:2, which(colnames(total_pop) %in% name))]

# Filter on countries
total_pop = total_pop[unique(total_pop$Country.Code) %in% unique(death$Code),]

# Cook Island, Niue & Tokelau is counted as a part of New Zealand
NZ = death %>%
  filter(Code %in% c("COK", "NZL", "NIU", "TKL")) %>%
  group_by(Year) %>%
  summarise_if(is.numeric, sum, na.rm = TRUE)
NZ$Code = "NZL"

death[death$Code == "NZL",] %>% 
  rows_update(NZ, by = c("Code", "Year"))

# Taiwan is counted as a part of China
CN = death %>%
  filter(Code %in% c("CHN", "TWN")) %>%
  group_by(Year) %>%
  summarise_if(is.numeric, sum, na.rm = TRUE)
CN$Code = "CHN"

death[death$Code == "CHN",] %>% 
  rows_update(CN, by = c("Year"))


# Remove them after they have been added 
cntrs = unique(death$Code)[which(!unique(death$Code) %in% unique(total_pop$Country.Code))] 
death =  death[-which(death$Code %in% cntrs),]

# Make table same format as original data
total_pop = melt(setDT(total_pop), id.vars = c("Country.Name", "Country.Code"),
                 measure.vars = c(names(total_pop)[3:length(names(total_pop))]))

# Download GDP data
countries = unique(total_pop$Country.Code)
GDP       = WDI(indicator = 'NY.GDP.MKTP.KD', country= countries, start=1990, end=2019)

# Set to same order
death     = death     %>% arrange(Code, Year)
total_pop = total_pop %>% arrange(Country.Code, variable)
GDP       = GDP       %>% arrange(iso3c, year)

# Update Data
death[, 'Population']                  = total_pop$value
death[, 'Gross Domestic Product(GDP)'] = GDP$NY.GDP.MKTP.KD

# Save dataset
write.csv(death, "/Users/dennisjonsson/Data-Visualization-Project/Data/Full Dataset")

