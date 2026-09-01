import json
import streamlit as st
import requests

from sources import SOURCES

st.set_page_config(page_title="NewsLens", page_icon="📰", layout="centered")

GROQ_MODEL = "llama-4-scout-17b-16e-instruct"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

LEVEL_INSTRUCTIONS = {
    "Beginner": (
        "Use simple, beginner-friendly language. Explain unfamiliar terms "
        "and basic concepts clearly."
    ),
    "Intermediate": (
        "Give useful context, relationships, and practical implications. "
        "Assume the reader knows the basic concepts."
    ),
    "Expert": (
        "Provide a deeper analytical explanation. Discuss nuance, trade-offs, "
        "uncertainties, limitations, and competing interpretations when relevant."
    ),
}


def build_prompt(topic, level, articles):
    article_text = []

    for index, article in enumerate(articles, start=1):
        article_text.append(
            f"""Article {index}
Title: {article.get("title", "Unknown title")}
Source: {article.get("source", {}).get("name", "Unknown source")}
Published: {article.get("publishedAt", "Unknown date")}
Description: {article.get("description", "No description available")}
Content: {article.get("content", "No content available")}
URL: {article.get("url", "")}"""
        )

    joined_articles = "\n\n".join(article_text)

    return f"""
You are NewsLens, a news-understanding assistant.

Topic: {topic}
Reader knowledge level: {level}

Instructions:
- {LEVEL_INSTRUCTIONS[level]}
- Use only the article information below.
- This is a news understanding and summarization task, not fact-checking.
- Do not claim that the articles are verified facts.
- If coverage is incomplete or uncertain, say so clearly.
- Do not add information that is not supported by the provided articles.
- Return Markdown using exactly these headings:

## Overall Summary
## Key Points
## Why It Matters
## Context / Explanation
## Things to Keep in Mind

Articles:
{joined_articles}
"""


def get_groq_response(prompt):
    try:
        groq_api_key = st.secrets["GROQ_API_KEY"]
    except (KeyError, FileNotFoundError):
        return None, "GROQ_API_KEY is missing. Add it to Streamlit secrets."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {groq_api_key}",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.3,
    }

    try:
        response = requests.post(
            GROQ_URL,
            headers=headers,
            json=payload,
            timeout=45,
        )
        data = response.json()

        if response.status_code != 200:
            error = data.get("error", {}).get("message", "Groq request failed.")
            return None, error

        choices = data.get("choices", [])
        if not choices:
            return None, "Groq did not return a response."

        text = choices[0]["message"]["content"]
        return text, None

    except requests.RequestException:
        return None, "Could not connect to Groq. Please try again."
    except (ValueError, KeyError, IndexError):
        return None, "Groq returned an unexpected response."


st.title("NewsLens")
st.caption("Understand recent news at your preferred knowledge level.")

topic = st.text_input(
    "News topic or keyword",
    placeholder="Example: artificial intelligence"
)

level = st.selectbox(
    "Choose your knowledge level",
    ["Beginner", "Intermediate", "Expert"]
)

if st.button("Analyze news", type="primary"):
    if not topic.strip():
        st.warning("Please enter a news topic or keyword.")
        st.stop()

    with st.spinner("Finding recent articles..."):
        articles, error = SOURCES["NewsAPI"](topic.strip())

    if error:
        st.error(f"NewsAPI error: {error}")
        st.stop()

    if not articles:
        st.info("No recent articles were found. Try a broader or different topic.")
        st.stop()

    prompt = build_prompt(topic.strip(), level, articles)

    with st.spinner("Creating your news explanation..."):
        summary, error = get_groq_response(prompt)

    if error:
        st.error(f"Groq error: {error}")
        st.stop()

    st.markdown(summary)

    st.divider()
    st.subheader("Original articles")

    for article in articles:
        source = article.get("source", {}).get("name", "Unknown source")
        date = article.get("publishedAt", "Unknown date")
        title = article.get("title", "Untitled article")
        url = article.get("url", "")

        st.markdown(f"**[{title}]({url})**")
        st.caption(f"{source} · {date}")
