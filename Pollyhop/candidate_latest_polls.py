import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# Function to scrape the Ballotpedia page and extract candidate information
def get_presidential_candidates(url):
    response = requests.get(url)
    response.raise_for_status()  # Ensure the request was successful
    soup = BeautifulSoup(response.text, 'html.parser')

    candidates_info = []

    # Find the section with "List of noteworthy candidates"
    noteworthy_section = soup.find(id="List_of_noteworthy_candidates")
    if noteworthy_section:
        noteworthy_list = noteworthy_section.find_next('ul')
        for li in noteworthy_list.find_all('li'):
            candidate = li.get_text()
            candidates_info.append(candidate)

    # Find the section with "Other candidates"
    other_section = soup.find(id="Other_candidates")
    if other_section:
        other_list = other_section.find_next('ul')
        for li in other_list.find_all('li'):
            candidate = li.get_text()
            candidates_info.append(candidate)

    return candidates_info

# Function to extract names and full party names from the candidate information
def extract_names_and_parties(candidates_info):
    # Regular expression to extract candidate names and their parties
    pattern = re.compile(r'([\w\s\.-]+(?:\s\w+)?(?:\spresidential campaign, 2024)?) \(([^)]+)\)')

    # Dictionary to map abbreviations to full party names
    party_mapping = {
        "D": "Democratic Party",
        "R": "Republican Party",
        "I": "Independent",
    }

    names_and_parties = []
    for candidate in candidates_info:
        match = pattern.search(candidate)
        if match:
            name, party = match.groups()
            # Clean the candidate name if it contains extra description
            if 'presidential campaign, 2024' in name:
                name = name.replace('presidential campaign, 2024', '').strip()
            full_party = party_mapping.get(party.strip(), party.strip())
            names_and_parties.append((name.strip(), full_party))

    return names_and_parties

# URL to scrape
url = "https://ballotpedia.org/Presidential_candidates,_2024"

# Get the list of presidential candidates and their parties
candidates_info = get_presidential_candidates(url)

# Extract and print the names and full party names
names_and_parties = extract_names_and_parties(candidates_info)
print("Extracted Candidate Names and Parties:")
for name, party in names_and_parties:
    print(f"{name}: {party}")

# Fetch the latest poll data
csv_url = 'https://projects.fivethirtyeight.com/polls/data/president_polls.csv'

# Define the path to save the downloaded CSV file
output_file = 'latest_polls.csv'

# Download the CSV file
response = requests.get(csv_url)
response.raise_for_status()  # Ensure the request was successful

# Save the CSV to a file
with open(output_file, 'wb') as file:
    file.write(response.content)

# Read the CSV
df = pd.read_csv(output_file)

# Ensure the start_date column is in datetime format
df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')

# Filter and display the latest poll data for the extracted candidates
candidate_names = [name for name, party in names_and_parties]
filtered_poll_data = df[df['candidate_name'].isin(candidate_names)].sort_values(by=['start_date'], ascending=False).drop_duplicates(subset=['candidate_name'])

# Sort the data by start date in descending order
latest_poll_data_sorted = filtered_poll_data.sort_values(by=['start_date'], ascending=False)

# Print the detailed latest poll data for extracted candidates
print("Latest Poll Data for Extracted Candidates (Detailed):")
print(latest_poll_data_sorted[['candidate_name', 'party', 'answer', 'pct', 'pollster', 'start_date', 'end_date', 'election_date']])

# Print the simplified latest poll data with candidate_name, party, and pct
print("\nLatest Poll Data for Extracted Candidates (Simplified):")
simplified_poll_data = latest_poll_data_sorted[['candidate_name', 'party', 'pct']]
print(simplified_poll_data)



