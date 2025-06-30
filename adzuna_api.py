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

def map_keywords_to_roles(keywords):
    """
    Map raw skill keywords to likely job titles.
    """
    roles = [KEYWORD_TO_ROLE[k] for k in keywords if k in KEYWORD_TO_ROLE]
    return list(set(roles))

def query_jobs(keywords, location, max_results=20):
    """
    Query Adzuna API using cleaned keywords and mapped roles.
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        return {"error": "Missing Adzuna credentials"}

    cleaned_keywords = clean_keywords(keywords)
    role_keywords = map_keywords_to_roles(cleaned_keywords)

    # ✅ Combine and format with OR logic for broader matching
    combined_terms = list(set(role_keywords + cleaned_keywords))
    search_terms = " OR ".join(combined_terms[:7])  # limit to 7 terms

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
        print("📡 Full API URL:", response.url)
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
