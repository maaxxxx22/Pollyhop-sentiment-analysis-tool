import requests
from textblob import TextBlob
import spacy

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

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

def extract_articles(search_results):
    articles = []
    for result in search_results.get("value", []):
        title = result.get("name", "")
        snippet = result.get("description", "")
        articles.append(f"{title} - {snippet}")
    return articles

def perform_sentiment_analysis(articles):
    sentiments = []
    for article in articles:
        blob = TextBlob(article)
        sentiment = blob.sentiment.polarity
        sentiments.append((article, sentiment))
    return sentiments

# Use your actual API key
bing_api_key = "552b1bf4baf347b98e75c259d1d61ac3"

# Query for Bing search
query = "Donald Trump Alabama"

# Get Bing search results
search_results = get_bing_search_results(bing_api_key, query)

# Extract articles from search results
articles = extract_articles(search_results)

# Perform sentiment analysis on articles
sentiments = perform_sentiment_analysis(articles)

# Calculate the average sentiment score
total_sentiment = sum(sentiment for _, sentiment in sentiments)
average_sentiment = total_sentiment / len(sentiments) if sentiments else 0

print("Sentiment Analysis of News Articles about Donald Trump in Alabama:")
for article, sentiment in sentiments:
    sentiment_label = "Positive" if sentiment > 0 else "Negative" if sentiment < 0 else "Neutral"
    print(f"Sentiment: {sentiment_label}, Score: {sentiment:.2f}")
    print(f"Article: {article}\n")

print(f"Average Sentiment Score: {average_sentiment:.2f}")
