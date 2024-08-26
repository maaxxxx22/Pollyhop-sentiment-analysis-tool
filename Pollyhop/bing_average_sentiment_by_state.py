import pandas as pd
import os
import shutil

def move_old_files(directory, old_files_dir, filenames):
    # Move specified files from the main directory to the old_files directory
    for filename in filenames:
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            shutil.move(file_path, os.path.join(old_files_dir, filename))

# Load the Bing data with sentiment
file_path = 'data/bing_data_with_sentiment.csv'
bing_data = pd.read_csv(file_path)

# Define the old files directory
old_files_directory = 'data1/old_data'

# Define the filenames to move
files_to_move = ['bing_average_sentiment_by_state.csv', 'bing_overall_average_sentiment_by_candidate.csv']

# Move old files before saving new ones
move_old_files('data1', old_files_directory, files_to_move)

# Calculate the average sentiment score for each state and candidate
average_sentiment_by_state = bing_data.groupby(['state', 'candidate']).agg({'sentiment': 'mean'}).reset_index()
average_sentiment_by_state.columns = ['State', 'Candidate', 'Average_Sentiment_Score']

# Save the result to a new CSV file
output_file = 'data1/bing_average_sentiment_by_state.csv'
average_sentiment_by_state.to_csv(output_file, index=False)

# Calculate the overall average sentiment score for each candidate across all states
bing_average_sentiment_by_candidate = bing_data.groupby('candidate').agg({'sentiment': 'mean'}).reset_index()
bing_average_sentiment_by_candidate.columns = ['Candidate', 'Overall_Average_Sentiment_Score']

# Save the overall average sentiment score to a new CSV file
overall_output_file = 'data1/bing_overall_average_sentiment_by_candidate.csv'
bing_average_sentiment_by_candidate.to_csv(overall_output_file, index=False)

# Display the results
print("Average Sentiment by State and Candidate:")
print(average_sentiment_by_state.head())
print("\nOverall Average Sentiment by Candidate:")
print(bing_average_sentiment_by_candidate)
