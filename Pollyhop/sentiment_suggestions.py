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

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

# Initialize KeyBERT model
kw_model = KeyBERT()

# Load the summarization pipeline
summarizer = pipeline("summarization")


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


# Function to extract main issues using NER and keyphrase extraction
def extract_issues_with_context(text):
    doc = nlp(text)
    issues = [ent.text for ent in doc.ents if
              ent.label_ in ["ORG", "GPE", "EVENT", "LAW", "NORP"]]  # Added 'LAW' and 'NORP'
    # Keyphrase extraction using KeyBERT
    keyphrases = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 2), stop_words='english', top_n=10)
    issues.extend([phrase[0] for phrase in keyphrases])
    # Capture relevant part of the article
    sentences = list(doc.sents)
    issue_snippets = {}
    for issue in issues:
        for sent in sentences:
            if issue in sent.text:
                issue_snippets[issue] = sent.text
                break
    return issue_snippets


# Function to analyze sentiment by issue
def analyze_sentiment_by_issue(articles):
    issue_sentiments = defaultdict(list)
    issue_context = {}
    for article, sentiment in articles:
        issue_snippets = extract_issues_with_context(article)
        for issue, snippet in issue_snippets.items():
            issue_sentiments[issue].append(sentiment)
            issue_context[issue] = snippet
    return issue_sentiments, issue_context


# Function to calculate average sentiment
def calculate_average_sentiment(issue_sentiments):
    average_sentiments = {issue: sum(sentiments) / len(sentiments) for issue, sentiments in issue_sentiments.items()}
    return average_sentiments


# Function to identify the weakest and strongest issue
def identify_issues(average_sentiments):
    if not average_sentiments:
        return None, None, None, None
    weakest_issue = min(average_sentiments, key=average_sentiments.get)
    strongest_issue = max(average_sentiments, key=average_sentiments.get)
    weakest_sentiment = average_sentiments[weakest_issue]
    strongest_sentiment = average_sentiments[strongest_issue]
    return weakest_issue, weakest_sentiment, strongest_issue, strongest_sentiment


# Function to find the most re-occurring issue
def find_most_recurring_issue(issue_sentiments, articles):
    all_issues = [issue for issue_list in issue_sentiments.keys() for issue in issue_list]
    if not all_issues:
        return None, None
    most_recurring_issue = Counter(all_issues).most_common(1)[0][0]

    # Find the article with the highest count of recurring issue keywords
    max_count = 0
    selected_article = ""
    for article in articles:
        count = sum(1 for word in article.split() if word in most_recurring_issue.split())
        if count > max_count:
            max_count = count
            selected_article = article

    # Ensure at least 3 keywords match
    if max_count >= 3:
        return most_recurring_issue, selected_article
    else:
        return None, None


# Pre-Canned Responses
pre_canned_responses_weak = [
    "Address the negative sentiment related to the article '{}'. Emphasize positive messaging and solutions.",
    "Engage with the community to improve perceptions related to the article '{}'. Consider town halls, Q&A sessions, or other engagement strategies.",
    "Highlight past successes or positive outcomes related to the article '{}'.",
    "Counteract the negative sentiment surrounding the article '{}' with factual information and positive testimonials.",
    "Use social media campaigns to improve the sentiment around the article '{}'. Share stories, achievements, and positive impacts.",
]

pre_canned_responses_strong = [
    "Capitalize on the positive sentiment related to the article '{}'. Reinforce positive messaging and maintain momentum.",
    "Use the positive sentiment surrounding the article '{}' to build stronger community relations.",
    "Highlight the successes mentioned in the article '{}' to further enhance your public image.",
    "Share the positive outcomes mentioned in the article '{}' widely to boost morale and support.",
    "Leverage the positive sentiment from the article '{}' in your campaigns and public communications.",
]

pre_canned_responses_recurring = [
    "Since the issue '{}' is frequently mentioned, ensure consistent and clear communication about it.",
    "Develop detailed FAQs and informational content around the issue '{}'.",
    "Proactively address the issue '{}' in your public statements and engagements.",
    "Monitor and respond to public sentiment about the issue '{}' regularly.",
    "Use the frequent mentions of '{}' to guide your strategic communications and policy focus.",
]


# Function to select the most relevant pre-canned response
def select_best_response(summary, responses):
    documents = [response.format(summary) for response in responses] + [summary]
    tfidf_vectorizer = TfidfVectorizer().fit_transform(documents)
    cosine_similarities = cosine_similarity(tfidf_vectorizer[-1], tfidf_vectorizer[:-1])
    best_response_index = np.argmax(cosine_similarities)
    return documents[best_response_index]


# Function to generate suggestions using pre-canned responses
def generate_suggestions(issue, sentiment, context, response_type):
    summary = summarize_text(context)
    best_response = select_best_response(summary, response_type)
    return best_response


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

print(f"Average Sentiment Score: {average_sentiment:.2f}\n")

# Analyze sentiment by issue
issue_sentiments, issue_context = analyze_sentiment_by_issue(sentiments)
average_issue_sentiments = calculate_average_sentiment(issue_sentiments)
print(f"Average Issue Sentiments: {average_issue_sentiments}")

# Identify weakest and strongest issue
weakest_issue, weakest_sentiment, strongest_issue, strongest_sentiment = identify_issues(average_issue_sentiments)
most_recurring_issue, recurring_article = find_most_recurring_issue(issue_sentiments, articles)

if weakest_issue:
    print(f"Weakest Issue: {weakest_issue}, Average Sentiment: {weakest_sentiment:.2f}\n")
    context = issue_context[weakest_issue]
    suggestions = generate_suggestions(weakest_issue, weakest_sentiment, context, pre_canned_responses_weak)
    print("Suggestions for Improvement on Weakest Issue:")
    print(suggestions)
else:
    print("No weakest issue found for sentiment analysis.")

if strongest_issue:
    print(f"Strongest Issue: {strongest_issue}, Average Sentiment: {strongest_sentiment:.2f}\n")
    context = issue_context[strongest_issue]
    suggestions = generate_suggestions(strongest_issue, strongest_sentiment, context, pre_canned_responses_strong)
    print("Suggestions for Capitalizing on Strongest Issue:")
    print(suggestions)

if most_recurring_issue:
    print(f"Most Recurring Issue: {most_recurring_issue}\n")
    context = recurring_article
    suggestions = generate_suggestions(most_recurring_issue, 0, context, pre_canned_responses_recurring)
    print("Suggestions for Addressing Most Recurring Issue:")
    print(suggestions)
else:
    print("No recurring issues found.")
