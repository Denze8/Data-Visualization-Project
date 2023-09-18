library(data.table)
library(tidyverse)
library(WDI)

# Import data
death     = read.csv("https://raw.githubusercontent.com/Denze8/Data-Visualization-Project/main/Data/cause_of_deaths.csv?token=GHSAT0AAAAAACHXHC7NOSJWTRNS4IFMBACOZIIEG7A")
total_pop = read.csv("https://raw.githubusercontent.com/Denze8/Data-Visualization-Project/main/Data/population.csv?token=GHSAT0AAAAAACHXHC7NUXI5CZJQUGBPI52UZIIEGIQ")

# Years in original data
name = paste(unique(death$Year))

# Filter pop-data on correct years
colnames(total_pop) = gsub("X", "", names(total_pop), fixed = TRUE) 
total_pop           = total_pop[, c(1:2, which(colnames(total_pop) %in% name))]

# Filter on countries
total_pop = total_pop[unique(total_pop$Country.Code) %in% unique(death$Code),]

# countries not in population data
cntrs = unique(death$Country.Territory)[which(!unique(death$Code) %in% unique(total_pop$Country.Code))] 
death = death %>%  filter(cntrs)

# Make table same format as original data
total_pop = setDT(total_pop)
total_pop = melt(total_pop, id.vars = c("Country.Name", "Country.Code"),
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
write.csv(death, "/Users/dennisjonsson/Documents/1. Datavidenskab/1. Semester/Data Visualization/Data/real.csv")
