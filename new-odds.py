import pandas as pd
from IPython.display import display
import math

# Load the uploaded files
drivers_df = pd.read_csv('f1db_csv/drivers.csv')
races_df = pd.read_csv('f1db_csv/races.csv')
results_df = pd.read_csv('f1db_csv/results.csv')
constructor_df = pd.read_csv('f1db_csv/constructors.csv')

# Display the first few rows of each dataframe to understand their structure
drivers_df.head(), races_df.head(), results_df.head()


# calc odds for drivers

# Filter races for 2021 to 2023
races_filtered_df = races_df[races_df['year'].between(2021, 2023)]

# Join the filtered races with results
results_filtered_df = pd.merge(results_df, races_filtered_df, on='raceId')

# Define functions to calculate probabilities for each category
display(results_filtered_df.columns)

display(results_filtered_df.iloc[:, [1, 2, 6, 8, 14, 15, 21]])


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
    results_filtered_df, ~results_filtered_df['statusId'].isin([1, 11, 12, 13, 14, 15, 16, 17, 18, 19]))

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

new_cols = ['Driver', 'Winner', 'Top 3',
            'Top 6', 'Top 10', 'Fastest Lap', 'DNF']
odds_df = odds_df[new_cols]
# Display the final DataFrame with odds for each driver
display(odds_df)

odds_cols = ['Winner', 'Top 3', 'Top 6', 'Top 10', 'Fastest Lap', 'DNF']
for col in odds_cols:
    odds_df[col] **= -1


odds_df.fillna(500, inplace=True)

display(odds_df)

odds_df.to_csv('_odds.csv', index=False)
