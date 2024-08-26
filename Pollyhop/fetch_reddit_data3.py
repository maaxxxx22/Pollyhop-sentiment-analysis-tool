import praw
import pandas as pd
from textblob import TextBlob
import re
import requests
from bs4 import BeautifulSoup


def get_reddit_instance():
    reddit = praw.Reddit(
        client_id='KzMIC1fcXoFiJ7_aUGe24Q',
        client_secret='6AqSj6QcZ5Y0JuGmkCch5SGBUGEqVw',
        user_agent='maaxxxx22_app/0.1 by maaxxxx22',
    )
    return reddit


def fetch_reddit_data(reddit, candidate_name, state):
    query = f"{candidate_name} {state}"
    subreddit = reddit.subreddit('politics')
    posts = []

    for submission in subreddit.search(query, limit=100):
        posts.append(
            [submission.title, submission.selftext, submission.created_utc, submission.score, submission.num_comments])

    df = pd.DataFrame(posts, columns=['title', 'selftext', 'created_utc', 'score', 'num_comments'])
    return df


def analyze_sentiment(text):
    analysis = TextBlob(text)
    return analysis.sentiment.polarity


def extract_candidates():
    # URL to scrape
    url = "https://ballotpedia.org/Presidential_candidates,_2024"

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

    # Get the list of presidential candidates and their parties
    candidates_info = get_presidential_candidates(url)

    # Extract and return the names and full party names
    names_and_parties = extract_names_and_parties(candidates_info)
    candidates = [{"name": name, "party": party} for name, party in names_and_parties]
    return candidates


def main():
    candidates = extract_candidates()
    reddit = get_reddit_instance()
    all_data = []

    for candidate in candidates:
        candidate_name = candidate['name']
        for state in states:
            reddit_data = fetch_reddit_data(reddit, candidate_name, state)
            reddit_data['candidate'] = candidate_name
            reddit_data['state'] = state
            reddit_data['sentiment'] = reddit_data['title'].apply(analyze_sentiment) + reddit_data['selftext'].apply(
                analyze_sentiment)
            all_data.append(reddit_data)

    all_posts = pd.concat(all_data, ignore_index=True)
    all_posts['average_sentiment'] = all_posts.groupby(['candidate', 'state'])['sentiment'].transform('mean')
    all_posts.to_csv('data1/reddit_data_with_sentiment.csv', index=False)

    overall_sentiment = all_posts.groupby('candidate')['average_sentiment'].mean().reset_index()
    overall_sentiment.to_csv('data1/overall_sentiment_by_candidate.csv', index=False)


if __name__ == "__main__":
    states = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware',
              'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
              'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana',
              'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Carolina',
              'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina',
              'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia',
              'Wisconsin', 'Wyoming']
    main()
