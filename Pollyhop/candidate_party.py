import requests
from bs4 import BeautifulSoup
import re


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
for name, party in names_and_parties:
    print(f"{name}: {party}")


