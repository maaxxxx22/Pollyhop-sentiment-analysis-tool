import pandas as pd
import os
import time
import imblearn

def append_to_csv(data, filename, max_retries=5, wait_time=1):
    for attempt in range(max_retries):
        try:
            if os.path.exists(filename):
                existing_data = pd.read_csv(filename)
                updated_data = pd.concat([existing_data, data], ignore_index=True)
                updated_data.to_csv(filename, index=False)
            else:
                data.to_csv(filename, index=False)
            print(f"Data successfully appended to {filename}")
            return
        except PermissionError as e:
            if attempt < max_retries - 1:
                print(f"Permission error encountered. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Failed to write to {filename} after {max_retries} attempts.")
                raise e

def append_new_column_to_existing_csv(new_data, filename, column_prefix="Combined_Ave_score"):
    if os.path.exists(filename):
        existing_data = pd.read_csv(filename)
        new_column_name = f"{column_prefix} {existing_data.shape[1] - 2}"
        existing_data[new_column_name] = new_data['Combined_Average_Sentiment_Score']
        existing_data.to_csv(filename, index=False)
    else:
        new_data.rename(columns={'Combined_Average_Sentiment_Score': f"{column_prefix} 1"}, inplace=True)
        new_data.to_csv(filename, index=False)

# Step 1: Import Candidate Names and Polling Data from candidate_latest_polls2.py
exec(open('candidate_latest_polls2.py').read())

# Correct variable names based on the provided debug output
candidate_parties = locals().get('names_and_parties')
latest_poll_data = locals().get('simplified_poll_data')

# Ensure data is loaded correctly
if candidate_parties is None or latest_poll_data is None:
    raise ValueError("Failed to load candidate_parties or latest_poll_data")

# Convert pct column to numeric, setting errors='coerce' to handle non-numeric values
latest_poll_data['pct'] = pd.to_numeric(latest_poll_data['pct'], errors='coerce')

# Fill N/A values in pct column with 0 (or another neutral value if appropriate)
latest_poll_data['pct'] = latest_poll_data['pct'].fillna(0)

# Display the imported candidate names and parties
print("Candidate Names and Parties from candidate_latest_polls2.py:")
print(candidate_parties)

# Display the imported latest polling data
print("\nLatest Polling Data from candidate_latest_polls2.py:")
print(latest_poll_data)

# Step 2: Import Historical Vote Percentage Prediction from predict_party_votes_percentage4.py
exec(open('predict_party_votes_percentage4.py').read())

# Historical data
historical_data = locals().get('historical_data')

# Ensure data is loaded correctly
if historical_data is None:
    raise ValueError("Failed to load historical_data")

# Retrieve class counts for historical vote percentages
class_counts = locals().get('class_counts')

# Ensure class counts are loaded correctly
if class_counts is None:
    raise ValueError("Failed to load class_counts")

# Display the class counts
print("\nClass distribution after resampling:")
print(class_counts)

# Calculate the total class distribution to get the percentages
total_class_distribution = class_counts.sum()

# Normalize the class distribution to get historical percentages
historical_percentages = (class_counts / total_class_distribution) * 100

# Display the calculated historical percentages
print("\nHistorical Percentages by Party:")
print(historical_percentages)

# Mapping from party abbreviations to full party names
party_mapping = {
    "DEM": "DEMOCRAT",
    "REP": "REPUBLICAN",
    "IND": "INDEPENDENT",
    "LIB": "LIBERTARIAN",
    "GRE": "GREEN",
    "CON": "CONSTITUTION"
}

# Function to get historical percentage based on party
def get_historical_percentage(party_abbr):
    full_party_name = party_mapping.get(party_abbr, "OTHER")
    return historical_percentages.get(full_party_name, historical_percentages['OTHER'])

# Add historical percentage to latest_poll_data
latest_poll_data['historical_pct'] = latest_poll_data['party'].apply(get_historical_percentage)

# Print latest_poll_data to check if the 'historical_pct' column is added
print("\nLatest Poll Data after adding historical percentage:")
print(latest_poll_data)

# Step 3: Import Sentiment Data from average_sentiment_by_state.py
exec(open('average_sentiment_by_state.py').read())

# Sentiment data from average_sentiment_by_state.py
average_sentiment_by_candidate = locals().get('average_sentiment_by_candidate')

# Ensure data is loaded correctly
if average_sentiment_by_candidate is None:
    raise ValueError("Failed to load average_sentiment_by_candidate")

# Scale the sentiment scores
scaling_factor = 10
average_sentiment_by_candidate['Overall_Average_Sentiment_Score'] *= scaling_factor

# Display the imported sentiment data
print("\nSentiment Data from average_sentiment_by_state.py:")
print(average_sentiment_by_candidate)

# Step 4: Import Sentiment Data from bing_average_sentiment_by_state.py
exec(open('bing_average_sentiment_by_state.py').read())

# Sentiment data from bing_average_sentiment_by_state.py
bing_average_sentiment_by_candidate = locals().get('bing_average_sentiment_by_candidate')

# Ensure data is loaded correctly
if bing_average_sentiment_by_candidate is None:
    raise ValueError("Failed to load bing_average_sentiment_by_candidate")

# Scale the sentiment scores
bing_average_sentiment_by_candidate['Overall_Average_Sentiment_Score'] *= scaling_factor

# Display the imported sentiment data
print("\nSentiment Data from bing_average_sentiment_by_state.py:")
print(bing_average_sentiment_by_candidate)

# Combining all data
# Ensure candidate names are consistent across datasets
latest_poll_data['candidate_name'] = latest_poll_data['candidate_name'].str.upper()
average_sentiment_by_candidate['Candidate'] = average_sentiment_by_candidate['Candidate'].str.upper()
bing_average_sentiment_by_candidate['Candidate'] = bing_average_sentiment_by_candidate['Candidate'].str.upper()

# Merge polling data with sentiment data from average_sentiment_by_state.py
combined_data = latest_poll_data.merge(average_sentiment_by_candidate, left_on='candidate_name', right_on='Candidate', how='left')

# Merge with sentiment data from bing_average_sentiment_by_state.py
combined_data = combined_data.merge(bing_average_sentiment_by_candidate, left_on='candidate_name', right_on='Candidate', how='left')

# Ensure the column names for sentiments match what we are expecting
combined_data.rename(columns={'Overall_Average_Sentiment_Score_x': 'average_sentiment_1', 'Overall_Average_Sentiment_Score_y': 'average_sentiment_2'}, inplace=True)

# Fill N/A values in sentiment columns with 0 (or another neutral value if appropriate)
combined_data['average_sentiment_1'] = combined_data['average_sentiment_1'].fillna(0)
combined_data['average_sentiment_2'] = combined_data['average_sentiment_2'].fillna(0)

# Print combined data to verify all columns
print("\nCombined Data with Poll, Historical, and Sentiment Scores:")
print(combined_data[['candidate_name', 'party', 'pct', 'historical_pct', 'average_sentiment_1', 'average_sentiment_2']])

# Save the combined data to a CSV file
combined_data.to_csv('combined_data_intermediate.csv', index=False)

# Calculate the final predicted percentage using weights
weights = {
    'polling': 0.40,
    'historical': 0.30,
    'sentiment_1': 0.15,
    'sentiment_2': 0.15
}

# Calculate the predicted percentage
combined_data['predicted_pct'] = (
    combined_data['pct'] * weights['polling'] +
    combined_data['historical_pct'] * weights['historical'] +
    (combined_data['average_sentiment_1'] * 100) * weights['sentiment_1'] +
    (combined_data['average_sentiment_2'] * 100) * weights['sentiment_2']
)

# Normalize the predicted percentages to sum up to 100
total_predicted = combined_data['predicted_pct'].sum()
combined_data['normalized_predicted_pct'] = (combined_data['predicted_pct'] / total_predicted) * 100

# Selecting the final columns
final_result = combined_data[['candidate_name', 'party', 'pct', 'historical_pct', 'average_sentiment_1', 'average_sentiment_2', 'predicted_pct', 'normalized_predicted_pct']]
print("\nFinal Predicted Percentages (Normalized):")
print(final_result)

# Save the final result to a CSV file
final_result.to_csv('final_predicted_percentages_normalized.csv', index=False)

# Detailed verification for Kamala Harris
kamala_harris_data = combined_data[combined_data['candidate_name'] == 'KAMALA HARRIS']

print("\nDetailed Verification for Kamala Harris:")
print(kamala_harris_data[['candidate_name', 'party', 'pct', 'historical_pct', 'average_sentiment_1', 'average_sentiment_2', 'predicted_pct', 'normalized_predicted_pct']])

# Calculate and append average sentiment by state to existing CSV file
bing_average_sentiment_by_state = pd.read_csv
bing_average_sentiment_by_state = pd.read_csv('data1/bing_average_sentiment_by_state.csv')
reddit_average_sentiment_by_state = pd.read_csv('data1/average_sentiment_by_state_candidate.csv')

# Merge Bing and Reddit sentiment data by State and Candidate to calculate the combined average sentiment score
combined_sentiment_by_state = pd.merge(bing_average_sentiment_by_state, reddit_average_sentiment_by_state, on=['State', 'Candidate'], suffixes=('_bing', '_reddit'))
combined_sentiment_by_state['Combined_Average_Sentiment_Score'] = combined_sentiment_by_state[['Average_Sentiment_Score_bing', 'Average_Sentiment_Score_reddit']].mean(axis=1)

# Append the combined average sentiment scores to an existing CSV file to track changes over time
combined_sentiment_filename = 'data1/combined_average_sentiment_by_state.csv'
append_new_column_to_existing_csv(combined_sentiment_by_state, combined_sentiment_filename)

# Print the combined sentiment by state
print("\nCombined Sentiment by State:")
print(combined_sentiment_by_state.head())

# Calculate and append average combined sentiment to final_sentiment_score.csv
average_combined_sentiment = final_result[['candidate_name', 'party', 'average_sentiment_1', 'average_sentiment_2']].copy()
average_combined_sentiment['average_combined_sentiment'] = average_combined_sentiment[['average_sentiment_1', 'average_sentiment_2']].mean(axis=1)

# Prepare the data to append
average_combined_sentiment_data = average_combined_sentiment[['candidate_name', 'party', 'average_combined_sentiment']]

# Append the average combined sentiment scores to an existing CSV file
average_combined_sentiment_filename = 'data/final_sentiment_score.csv'
append_to_csv(average_combined_sentiment_data, average_combined_sentiment_filename)

# Print the average combined sentiment data
print("\nAverage Combined Sentiment by Candidate:")
print(average_combined_sentiment_data.head())
