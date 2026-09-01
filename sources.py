import streamlit as st
import requests

NEWS_API_URL = "https://newsapi.org/v2/everything"

def get_news(topic):
    """Fetch up to five recent articles for a topic from NewsAPI."""
    try:
        news_api_key = st.secrets["NEWS_API_KEY"]
    except (KeyError, FileNotFoundError):
        return [], "NEWS_API_KEY is missing. Add it to Streamlit secrets."

    params = {
        "q": topic,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": news_api_key,
    }

    try:
        response = requests.get(NEWS_API_URL, params=params, timeout=15)
        data = response.json()

        if response.status_code != 200:
            return [], data.get("message", "NewsAPI request failed.")

        articles = [
            article for article in data.get("articles", [])
            if article.get("title") and article.get("url")
        ]

        return articles, None

    except requests.RequestException:
        return [], "Could not connect to NewsAPI. Please try again."
    except ValueError:
        return [], "NewsAPI returned an unexpected response."


SOURCES = {
    "NewsAPI": get_news
}
