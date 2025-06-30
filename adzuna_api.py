import os
import requests
import re

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
ADZUNA_COUNTRY = os.getenv("ADZUNA_COUNTRY", "us")

# 🔁 Optional: Mapping generic skills to common roles
KEYWORD_TO_ROLE = {
    "html": "frontend developer",
    "css": "frontend developer",
    "javascript": "frontend developer",
    "python": "software engineer",
    "sql": "data analyst",
    "react": "frontend developer",
    "aws": "cloud engineer",
    "django": "python developer",
    "node": "backend developer",
    "java": "backend developer",
}


def clean_keywords(text):
    """
    Clean and normalize skills/summary to extract search-friendly keywords.
    """
    if not text:
        return []
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)  # remove punctuation
    keywords = re.findall(r"\b\w{3,}\b", text)  # keep words with 3+ letters
    return list(set(keywords))


def query_jobs(keywords, location, max_results=20):
    """
    Query Adzuna with smart extracted keywords and location.
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        return {"error": "Missing Adzuna credentials"}
