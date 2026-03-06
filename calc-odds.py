import pandas as pd
from IPython.display import display

# Load the provided CSV files
constructors_df = pd.read_csv('f1db_csv/constructors.csv')
drivers_df = pd.read_csv('f1db_csv/drivers.csv')
qualifying_df = pd.read_csv('f1db_csv/qualifying.csv')
races_df = pd.read_csv('f1db_csv/races.csv')
results_df = pd.read_csv('f1db_csv/results.csv')
odds_input_2024_df = pd.read_csv('odds_input_2024.csv')

# Display the first few rows of each DataFrame to understand their structure
dataframes = {
    "Constructors": constructors_df,
    "Drivers": drivers_df,
    "Qualifying": qualifying_df,
    "Races": races_df,
    "Results": results_df,
    "Odds Input 2022": odds_input_2024_df
}

for name, df in dataframes.items():
    print(f"{name} DataFrame preview:")
    print(df.head())
    print("\n")


# Filter races from the last two years (2022 and 2023)
recent_races_df = races_df[(races_df['year'] == 2022)
                           | (races_df['year'] == 2023)]

# Merge the recent races with the results to get a comprehensive dataset for analysis
recent_results_df = pd.merge(
    recent_races_df, results_df, on='raceId', how='inner')

# Display the structure of the merged data to confirm the successful merge
print(recent_results_df.head())


# Analyzing driver performance based on finishing positions and points scored
# Grouping data by driverId and calculating average finishing position and total points

driver_performance = recent_results_df.groupby('driverId').agg(
    average_finish=pd.NamedAgg(column='positionOrder', aggfunc='mean'),
    total_points=pd.NamedAgg(column='points', aggfunc='sum')
).reset_index()

# Sorting drivers based on performance metrics for better understanding
driver_performance_sorted = driver_performance.sort_values(
    by=['total_points', 'average_finish'], ascending=[False, True])

display_driver_performance = driver_performance_sorted.merge(
    drivers_df, on='driverId')
# Displaying the sorted performance metrics
display(display_driver_performance[
    ['driverId', 'forename', 'surname', 'average_finish', 'total_points']])


# Estimation of odds based on performance metrics
# Normalizing the metrics and calculating a score for each driver
# Lower scores will indicate better performance

# Normalizing the average finish positions and total points
# The normalization is done in such a way that for both metrics, lower values are better
max_points = driver_performance_with_names['total_points'].max()
driver_performance_with_names['normalized_finish'] = 1 / \
    driver_performance_with_names['average_finish']
driver_performance_with_names['normalized_points'] = driver_performance_with_names['total_points'] / max_points

# Calculating a combined score based on normalized metrics
# Giving equal weight to both normalized finish and normalized points
driver_performance_with_names['score'] = 0.5 * driver_performance_with_names['normalized_finish'] + \
    0.5 * driver_performance_with_names['normalized_points']

# Inverting the score to calculate odds, higher scores now indicate higher odds
driver_performance_with_names['odds'] = 1 / \
    driver_performance_with_names['score']

# Sorting drivers based on odds, lower odds are better
driver_performance_with_names_sorted = driver_performance_with_names.sort_values(
    by='odds')

# Selecting relevant columns for the final odds presentation
final_odds = driver_performance_with_names_sorted[['Driver', 'Team', 'odds']]

# Displaying the final odds estimation
final_odds.head()


# Filter races for 2021 to 2023
races_filtered_df = races_df[races_df['year'].isin([2021, 2022, 2023])]

# Join the filtered races with results
results_filtered_df = pd.merge(results_df, races_filtered_df, on='raceId')

# Define functions to calculate probabilities for each category


def calculate_probability(df, condition):
    total_races = df['raceId'].nunique()
    return df[condition].groupby('driverId').size().div(total_races).fillna(0)


# Calculate probabilities
winner_probability = calculate_probability(
    results_filtered_df, results_filtered_df['positionOrder'] == 1)
top3_probability = calculate_probability(
    results_filtered_df, results_filtered_df['positionOrder'] <= 3)
top6_probability = calculate_probability(
    results_filtered_df, results_filtered_df['positionOrder'] <= 6)
top10_probability = calculate_probability(
    results_filtered_df, results_filtered_df['positionOrder'] <= 10)
fastest_lap_probability = calculate_probability(
    results_filtered_df, results_filtered_df['rank'] == '1')
dnf_probability = calculate_probability(
    results_filtered_df, results_filtered_df['statusId'] != 1)

# Combine all probabilities into a single DataFrame
probabilities_df = pd.concat([winner_probability, top3_probability, top6_probability,
                             top10_probability, fastest_lap_probability, dnf_probability], axis=1)
probabilities_df.columns = ['Winner', 'Top 3',
                            'Top 6', 'Top 10', 'Fastest Lap', 'DNF']
probabilities_df.reset_index(inplace=True)

# Merge with drivers DataFrame to get driver names
odds_df = pd.merge(probabilities_df, drivers_df[[
                   'driverId', 'forename', 'surname']], on='driverId')
odds_df['Driver'] = odds_df['forename'] + ' ' + odds_df['surname']
odds_df.drop(['driverId', 'forename', 'surname'], axis=1, inplace=True)

# Display the final DataFrame with odds for each driver
odds_df.head()
