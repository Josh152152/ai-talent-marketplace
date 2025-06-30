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

    cleaned_keywords = clean_keywords(keywords)
    search_terms = " ".join(cleaned_keywords[:5])  # Limit to top 5

    print("🔍 Adzuna Search Query:", search_terms)
    print("📍 Location:", location)

    base_url = f"https://api.adzuna.com/v1/api/jobs/{ADZUNA_COUNTRY}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": search_terms,
        "where": location,
        "results_per_page": max_results,
        "content-type": "application/json"
    }

    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            print("🧾 Raw Adzuna result count:", data.get("count", 0))
print("📦 Raw job titles:")
for job in data.get("results", []):
    print("-", job.get("title"))
            return {
                "count": data.get("count", 0),
                "examples": [job["title"] for job in data.get("results", [])]
            }
        else:
            print("❌ Adzuna API error:", response.status_code, response.text)
            return {
                "error": "Adzuna API request failed",
                "status": response.status_code,
                "details": response.text
            }
    except Exception as e:
        print(f"🔥 Exception during Adzuna request: {e}")
        return {"error": str(e)}
