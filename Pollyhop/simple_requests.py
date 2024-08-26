# simple_requests.py
import requests

def fetch_google_homepage():
    try:
        print("Attempting to fetch Google homepage...")
        response = requests.get("https://www.google.com")
        print(f"Received status code: {response.status_code}")
        return response.status_code
    except requests.RequestException as e:
        print(f"An error occurred: {str(e)}")
        return f"An error occurred: {str(e)}"

if __name__ == "__main__":
    print(fetch_google_homepage())
