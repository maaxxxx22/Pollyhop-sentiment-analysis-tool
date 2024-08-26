import os
import requests
from bs4 import BeautifulSoup
from candidate_latest_polls2 import extract_names_and_parties, get_presidential_candidates

# Define a function to get Ballotpedia URLs for candidates
def get_ballotpedia_urls(candidates):
    base_url = "https://ballotpedia.org/"
    urls = {}
    for candidate in candidates:
        name = candidate.replace(" ", "_")
        urls[candidate] = f"{base_url}{name}"
    return urls

# Directory to save images
image_folder = "images"
if not os.path.exists(image_folder):
    os.makedirs(image_folder)

def get_image_url(ballotpedia_url):
    print(f"Accessing Ballotpedia URL: {ballotpedia_url}")
    response = requests.get(ballotpedia_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    image_tag = soup.find('img', {'class': 'widget-img'})
    if image_tag:
        image_url = image_tag['src']
        print(f"Found image URL: {image_url}")
        return image_url
    return None

def download_image(url, filename):
    response = requests.get(url)
    with open(filename, 'wb') as file:
        file.write(response.content)

# URL to scrape
url = "https://ballotpedia.org/Presidential_candidates,_2024"

# Get the list of presidential candidates and their parties
candidates_info = get_presidential_candidates(url)

# Extract candidate names
names_and_parties = extract_names_and_parties(candidates_info)
candidates = [name for name, party in names_and_parties]

# Get Ballotpedia URLs
urls = get_ballotpedia_urls(candidates)

for candidate in candidates:
    image_path = os.path.join(image_folder, f"{candidate}.jpg")
    print(f"Image path for {candidate}: {image_path}")
    if not os.path.exists(image_path):
        print(f"Downloading image for {candidate}...")
        image_url = get_image_url(urls.get(candidate))
        if image_url:
            download_image(image_url, image_path)
        else:
            print(f"Image not found for {candidate}!")
    else:
        print(f"Image for {candidate} already exists. Skipping download.")
