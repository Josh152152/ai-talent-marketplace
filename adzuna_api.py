# adzuna_api.py

import os
import requests
import re

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
ADZUNA_COUNTRY = os.getenv("ADZUNA_COUNTRY", "us")


def clean_keywords(text):
    """
    Clean and normalize skills/summary to extract search-friendly keywords.
    """
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)  # remove punctuation
    keywords = re.findall(r"\b\w{3,}\b", text)  # keep words with 3+ letters
    return list(set(keywords))


def query_jobs(keywords, location, max_results=20):
    """
    Query Adzuna with smart extracted keywords.
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        return {"error": "Missing Adzuna credentials"}

    cleaned_keywords = clean_keywords(keywords)
    search_terms = " ".join(cleaned_keywords[:5])  # limit for now

    base_url = f"https://api.adzuna.com/v1/api/jobs/{ADZUNA_COUNTRY}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": search_terms,
        "where": location,
        "results_per_page": max_results,
        "content-type": "application/json"
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return {
            "count": data.get("count", 0),
            "examples": [job["title"] for job in data.get("results", [])]
        }
    else:
        print("❌ Adzuna API error:", response.status_code, response.text)
        return {"error": "Adzuna API request failed", "status": response.status_code}
