import pandas as pd
import requests
import os

# URL of the CSV file
csv_url = 'https://projects.fivethirtyeight.com/polls/data/president_polls.csv'

# Define the path to the data directory and ensure it exists
data_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
os.makedirs(data_directory, exist_ok=True)

# Path to save the downloaded CSV file
output_file = os.path.join(data_directory, 'latest_polls.csv')

# Download the CSV file
response = requests.get(csv_url)
response.raise_for_status()  # Ensure the request was successful

# Save the CSV to a file
try:
    with open(output_file, 'wb') as file:
        file.write(response.content)
    print(f"CSV downloaded and saved to {output_file}")
except PermissionError as e:
    print(f"Permission denied: {e}")
except Exception as e:
    print(f"An error occurred: {e}")

# Optionally, read the CSV and print the first few rows
try:
    df = pd.read_csv(output_file)
    print(df.head())
except Exception as e:
    print(f"Failed to read the CSV file: {e}")

