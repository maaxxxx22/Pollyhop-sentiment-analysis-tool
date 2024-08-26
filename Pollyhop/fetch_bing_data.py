import os

os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

import re
import requests
from textblob import TextBlob
import spacy
from collections import defaultdict, Counter
from keybert import KeyBERT
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

# Initialize KeyBERT model
kw_model = KeyBERT()

# Load the summarization pipeline with a specified model
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# Function to remove HTML tags
def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

# Function to extract clean sentences
def extract_clean_sentences(text):
    text = remove_html_tags(text)
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]
    return sentences

# Function to summarize text
def summarize_text(text, max_length=30, min_length=10):
    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return summary[0]['summary_text']

# Function to get Bing search results
def get_bing_search_results(api_key, query):
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {
        "q": query,
        "textDecorations": True,
        "textFormat": "HTML",
        "cc": "US",
        "setLang": "EN"
    }
    response = requests.get("https://api.bing.microsoft.com/v7.0/news/search", headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()
    return search_results

# Function to extract articles from search results
def extract_articles(search_results):
    articles = []
    for result in search_results.get("value", []):
        title = result.get("name", "")
        snippet = result.get("description", "")
        articles.append(f"{title} - {snippet}")
    return articles

# Function to perform sentiment analysis on articles
def perform_sentiment_analysis(articles):
    sentiments = []
    for article in articles:
        blob = TextBlob(article)
        sentiment = blob.sentiment.polarity
        sentiments.append((article, sentiment))
    return sentiments

# Use your actual API key
bing_api_key = "552b1bf4baf347b98e75c259d1d61ac3"

# Function to get presidential candidates from Ballotpedia
def get_presidential_candidates(url):
    response = requests.get(url)
    response.raise_for_status()
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

# Function to process each candidate in each state
def process_candidates(candidates, states):
    results = []

    for candidate, party in candidates:
        for state in states:
            query = f"{candidate} {state}"

            # Get Bing search results
            search_results = get_bing_search_results(bing_api_key, query)

            # Extract articles from search results
            articles = extract_articles(search_results)

            # Perform sentiment analysis on articles
            sentiments = perform_sentiment_analysis(articles)

            # Calculate the average sentiment score
            total_sentiment = sum(sentiment for _, sentiment in sentiments)
            average_sentiment = total_sentiment / len(sentiments) if sentiments else 0

            for article, sentiment in sentiments:
                results.append({
                    "title": article.split(" - ")[0],
                    "selftext": "",
                    "created_utc": "N/A",  # Placeholder as we don't have this data from Bing
                    "score": "N/A",       # Placeholder as we don't have this data from Bing
                    "num_comments": "N/A", # Placeholder as we don't have this data from Bing
                    "candidate": candidate,
                    "state": state,
                    "sentiment": sentiment,
                    "average_sentiment": average_sentiment
                })

    return results

# URL to scrape for candidate names and parties
url = "https://ballotpedia.org/Presidential_candidates,_2024"

# Extract candidates
candidates_info = get_presidential_candidates(url)
candidates = extract_names_and_parties(candidates_info)

# List of all states
states = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware',
          'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
          'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana',
          'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Carolina',
          'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina',
          'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia',
          'Wisconsin', 'Wyoming']

# Process each candidate in each state
results = process_candidates(candidates, states)

# Create a DataFrame from the results
df = pd.DataFrame(results)

# Save the DataFrame to a CSV file
output_file = 'data/bing_data_with_sentiment.csv'
df.to_csv(output_file, index=False)

# Display the DataFrame
print(df)
