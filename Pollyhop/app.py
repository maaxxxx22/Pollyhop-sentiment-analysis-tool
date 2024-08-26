from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import time
import re
import subprocess
import requests
from textblob import TextBlob
from bs4 import BeautifulSoup
from collections import defaultdict, Counter
from keybert import KeyBERT
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

app = Flask(__name__, static_url_path='/static')

# Global variable to track progress
progress = {'current_step': 0, 'total_steps': 3}

# Mapping of state names to state abbreviations
state_abbrev = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
    'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
    'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
    'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
    'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
    'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
    'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
    'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
    'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
    'Wisconsin': 'WI', 'Wyoming': 'WY'
}

def fetch_bing_data(bing_api_key, states, candidates):
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
                    "created_utc": "N/A",
                    "score": "N/A",
                    "num_comments": "N/A",
                    "candidate": candidate,
                    "state": state,
                    "sentiment": sentiment,
                    "average_sentiment": average_sentiment
                })

    return pd.DataFrame(results)



def fetch_reddit_data(states, candidates):
    import praw

    reddit = praw.Reddit(
        client_id='KzMIC1fcXoFiJ7_aUGe24Q',
        client_secret='6AqSj6QcZ5Y0JuGmkCch5SGBUGEqVw',
        user_agent='maaxxxx22_app/0.1 by maaxxxx22',
    )

    def analyze_sentiment(text):
        analysis = TextBlob(text)
        return analysis.sentiment.polarity

    all_data = []

    for candidate in candidates:
        candidate_name = candidate['name']
        for state in states:
            subreddit = reddit.subreddit('politics')
            posts = []
            query = f"{candidate_name} {state}"

            for submission in subreddit.search(query, limit=100):
                posts.append(
                    [submission.title, submission.selftext, submission.created_utc, submission.score, submission.num_comments])

            df = pd.DataFrame(posts, columns=['title', 'selftext', 'created_utc', 'score', 'num_comments'])
            df['candidate'] = candidate_name
            df['state'] = state
            df['sentiment'] = df['title'].apply(analyze_sentiment) + df['selftext'].apply(analyze_sentiment)
            all_data.append(df)

    return pd.concat(all_data, ignore_index=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file:
        df = pd.read_csv(file)

        # Normalize column names for consistency
        df.columns = df.columns.str.strip().str.lower()

        # Print the column names for debugging
        print("Uploaded CSV Columns:", df.columns.tolist())

        data = df.to_dict(orient='records')
        summary = {
            'average_sentiment_1': df['average_sentiment_1'].mean(),
            'average_sentiment_2': df['average_sentiment_2'].mean(),
            'average_predicted_pct': df['predicted_pct'].mean(),
        }
        return jsonify({'data': data, 'summary': summary})
    return jsonify({'error': 'No file uploaded'})

@app.route('/candidate/<name>')
def candidate(name):
    df = pd.read_csv('data/combined_average_sentiment_by_state.csv')

    # Normalize column names for consistency
    df.columns = df.columns.str.strip().str.lower()

    # Print the cleaned column names for debugging
    print("Candidate CSV Columns:", df.columns.tolist())

    # Normalize candidate names for consistency
    df['candidate'] = df['candidate'].str.strip().str.lower()
    name = name.strip().lower()

    # Print the candidate name for debugging
    print("Candidate Name:", name)

    # Select the rows for the specified candidate
    candidate_data = df[df['candidate'] == name]

    # Print the filtered data for debugging
    print("Filtered Candidate Data:", candidate_data)

    # Convert state names to abbreviations
    candidate_data['state'] = candidate_data['state'].map(state_abbrev)

    # Dynamically select columns starting with 'combined_ave_score'
    sentiment_columns = [col for col in df.columns if col.startswith('combined_ave_score')]

    # Extract state and sentiment scores for the candidate
    data = {
        'states': candidate_data['state'].unique().tolist(),
        'sentiments': {col: candidate_data.groupby('state')[col].mean().tolist() for col in sentiment_columns}
    }

    # Prepare data for the map
    # Only select numeric columns for the groupby and mean operation
    numeric_columns = candidate_data.select_dtypes(include=[np.number]).columns
    map_data = candidate_data.groupby('state')[numeric_columns].mean().reset_index()

    map_data = map_data[['state', 'combined_ave_score 3', 'combined_ave_score 4']]

    # Load final sentiment score over time for the candidate
    df_sentiment = pd.read_csv('data/final_sentiment_score.csv')
    df_sentiment.columns = df_sentiment.columns.str.strip().str.lower()
    print(df_sentiment.columns)  # Debugging line to print the column names
    df_sentiment['candidate_name'] = df_sentiment['candidate_name'].str.strip().str.lower()

    # Dynamically select columns starting with 'average_combined_sentiment_'
    sentiment_score_columns = [col for col in df_sentiment.columns if col.startswith('average_combined_sentiment_')]

    candidate_sentiment = df_sentiment[df_sentiment['candidate_name'] == name][sentiment_score_columns].T
    print(candidate_sentiment.columns)
    print(candidate_sentiment.shape)

    candidate_sentiment.columns = ['sentiment_score']
    candidate_sentiment['date'] = sentiment_score_columns
    candidate_sentiment = candidate_sentiment.set_index('date').to_dict()['sentiment_score']



    # Print the data for debugging
    print("Sentiment Columns:", sentiment_columns)
    print("Data:", data)
    print("Map Data:", map_data)
    print("Candidate Sentiment Data:", candidate_sentiment)

    return render_template('candidate.html', name=name, data=data, sentiment_columns=sentiment_columns,
                           map_data=map_data.to_dict(orient='records'), candidate_sentiment=candidate_sentiment)


progress = {'current_step': 0, 'total_steps': 3}

def update_progress(step):
    progress['current_step'] = step
    progress['progress'] = (progress['current_step'] / progress['total_steps']) * 100



def run_test4_script():
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


    # Mapping from party abbreviations to full party names
    party_mapping = {
        "DEM": "DEMOCRAT",
        "REP": "REPUBLICAN",
        "IND": "INDEPENDENT",
        "LIB": "LIBERTARIAN",
        "GRE": "GREEN",
        "CON": "CONSTITUTION"
    }

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
    combined_data = latest_poll_data.merge(average_sentiment_by_candidate, left_on='candidate_name',
                                           right_on='Candidate', how='left')

    # Merge with sentiment data from bing_average_sentiment_by_state.py
    combined_data = combined_data.merge(bing_average_sentiment_by_candidate, left_on='candidate_name',
                                        right_on='Candidate', how='left')

    # Ensure the column names for sentiments match what we are expecting
    combined_data.rename(columns={'Overall_Average_Sentiment_Score_x': 'average_sentiment_1',
                                  'Overall_Average_Sentiment_Score_y': 'average_sentiment_2'}, inplace=True)

    # Fill N/A values in sentiment columns with 0 (or another neutral value if appropriate)
    combined_data['average_sentiment_1'] = combined_data['average_sentiment_1'].fillna(0)
    combined_data['average_sentiment_2'] = combined_data['average_sentiment_2'].fillna(0)

    # Print combined data to verify all columns
    print("\nCombined Data with Poll, Historical, and Sentiment Scores:")
    print(combined_data[
              ['candidate_name', 'party', 'pct', 'historical_pct', 'average_sentiment_1', 'average_sentiment_2']])

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
    final_result = combined_data[
        ['candidate_name', 'party', 'pct', 'historical_pct', 'average_sentiment_1', 'average_sentiment_2',
         'predicted_pct', 'normalized_predicted_pct']]
    print("\nFinal Predicted Percentages (Normalized):")
    print(final_result)

    # Save the final result to a CSV file
    final_result.to_csv('final_predicted_percentages_normalized.csv', index=False)

    # Detailed verification for Kamala Harris
    kamala_harris_data = combined_data[combined_data['candidate_name'] == 'KAMALA HARRIS']

    print("\nDetailed Verification for Kamala Harris:")
    print(kamala_harris_data[
              ['candidate_name', 'party', 'pct', 'historical_pct', 'average_sentiment_1', 'average_sentiment_2',
               'predicted_pct', 'normalized_predicted_pct']])

    # Calculate and append average sentiment by state to existing CSV file
    bing_average_sentiment_by_state = pd.read_csv
    bing_average_sentiment_by_state = pd.read_csv('data1/bing_average_sentiment_by_state.csv')
    reddit_average_sentiment_by_state = pd.read_csv('data1/average_sentiment_by_state_candidate.csv')

    # Merge Bing and Reddit sentiment data by State and Candidate to calculate the combined average sentiment score
    combined_sentiment_by_state = pd.merge(bing_average_sentiment_by_state, reddit_average_sentiment_by_state,
                                           on=['State', 'Candidate'], suffixes=('_bing', '_reddit'))
    combined_sentiment_by_state['Combined_Average_Sentiment_Score'] = combined_sentiment_by_state[
        ['Average_Sentiment_Score_bing', 'Average_Sentiment_Score_reddit']].mean(axis=1)

    # Append the combined average sentiment scores to an existing CSV file to track changes over time
    combined_sentiment_filename = 'data1/combined_average_sentiment_by_state.csv'
    append_new_column_to_existing_csv(combined_sentiment_by_state, combined_sentiment_filename)

    # Print the combined sentiment by state
    print("\nCombined Sentiment by State:")
    print(combined_sentiment_by_state.head())

    # Calculate and append average combined sentiment to final_sentiment_score.csv
    average_combined_sentiment = final_result[
        ['candidate_name', 'party', 'average_sentiment_1', 'average_sentiment_2']].copy()
    average_combined_sentiment['average_combined_sentiment'] = average_combined_sentiment[
        ['average_sentiment_1', 'average_sentiment_2']].mean(axis=1)

    # Prepare the data to append
    average_combined_sentiment_data = average_combined_sentiment[
        ['candidate_name', 'party', 'average_combined_sentiment']]

    # Append the average combined sentiment scores to an existing CSV file
    average_combined_sentiment_filename = 'data/final_sentiment_score.csv'
    append_to_csv(average_combined_sentiment_data, average_combined_sentiment_filename)

    # Print the average combined sentiment data
    print("\nAverage Combined Sentiment by Candidate:")
    print(average_combined_sentiment_data.head())


@app.route('/fetch-new-data', methods=['POST'])
def fetch_new_data():
    try:
        update_progress(0)  # Start progress

        # Example data to simulate candidates and API key
        candidates = [
            {"name": "Joe Biden", "party": "DEM"},
            {"name": "Donald Trump", "party": "REP"},
            {"name": "Kamala Harris", "party": "DEM"}
        ]

        bing_api_key = "552b1bf4baf347b98e75c259d1d61ac3"
        states = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware',
                  'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky',
                  'Louisiana',
                  'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana',
                  'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Carolina',
                  'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina',
                  'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia',
                  'Wisconsin', 'Wyoming']

        # Try to fetch Bing data
        try:
            bing_data_df = fetch_bing_data(bing_api_key, states, candidates)
            if bing_data_df is None:
                raise Exception("Quota exceeded for Bing API.")
            bing_output_file = 'data/bing_data_with_sentiment.csv'
            bing_data_df.to_csv(bing_output_file, index=False)
            update_progress(33)  # 33% progress
        except Exception as e:
            print(f"An error occurred while fetching Bing data: {str(e)}")
            update_progress(33)  # Update progress even if it fails

        # Fetch Reddit data
        try:
            reddit_data_df = fetch_reddit_data(states, candidates)
            reddit_output_file = 'data/reddit_data_with_sentiment.csv'
            reddit_data_df.to_csv(reddit_output_file, index=False)
            update_progress(66)  # 66% progress
        except Exception as e:
            update_progress(100)
            return jsonify({'error': f'An error occurred with Reddit: {str(e)}'})

        # Run the final analysis script after fetching data
        try:
            run_test4_script()  # This will execute the steps from test4.py that process the data
            update_progress(100)  # Final step completed
            return jsonify({'message': 'Data fetched and processed successfully.'})
        except Exception as e:
            update_progress(100)
            return jsonify({'error': f'An error occurred in the final script: {str(e)}'})

    except Exception as e:
        update_progress(100)
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'})


@app.route('/progress')
def progress_status():
    global progress
    progress_percentage = (progress['current_step'] / progress['total_steps']) * 100
    return jsonify({'progress': progress_percentage})



if __name__ == '__main__':
    app.run(debug=True)