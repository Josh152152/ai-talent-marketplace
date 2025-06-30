import os
import requests
import re

# Load credentials from environment
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

# 🔁 Map skills to likely job titles
KEYWORD_TO_ROLE = {
    "html": "frontend developer",
    "css": "frontend developer",
    "javascript": "frontend developer",
    "react": "frontend developer",
    "python": "software engineer",
    "django": "python developer",
    "flask": "python developer",
    "sql": "data analyst",
    "aws": "cloud engineer",
    "node": "backend developer",
    "java": "backend developer",
    "api": "backend developer"
}

def clean_keywords(text):
    """
    Extract normalized, alphanumeric keywords.
    """
    if not text:
        return []
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return list(set(re.findall(r"\b\w{3,}\b", text)))

def map_keywords_to_roles(keywords):
    """
    Translate keywords to job roles if applicable.
    """
    return list(set(KEYWORD_TO_ROLE[k] for k in keywords if k in KEYWORD_TO_ROLE))

def detect_country(location):
    """
    Simple heuristic to decide country code for Adzuna API based on location string.
    """
    if not location:
        return "gb"  # default fallback

    loc = location.lower()
    us_cities = ["new york", "san francisco", "los angeles", "chicago", "seattle", "boston", "austin", "washington"]

    if any(city in loc for city in us_cities) or "united states" in loc or "usa" in loc:
        return "us"
    else:
        return "gb"

def query_jobs(keywords, location="London", max_results=10):
    """
    Query Adzuna API with cleaned and mapped search terms and dynamic country.
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        return {"error": "Missing Adzuna credentials"}

    country_code = detect_country(location)

    # Clean and map
    keyword_list = clean_keywords(keywords)
    role_terms = map_keywords_to_roles(keyword_list)

    # Prefer role terms, fallback to keywords
    search_terms = " ".join(role_terms[:3]) if role_terms else " ".join(keyword_list[:3])

    print("🔍 Adzuna Search Query:", search_terms)
    print("📍 Location:", location)
    print("🌍 Using country code:", country_code)

    url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": search_terms,
        "where": location,
        "results_per_page": max_results,
    }

    print("📡 Full API URL:", url + "?" + "&".join([f"{k}={v}" for k, v in params.items()]))

    try:
        response = requests.get(url, params=params)
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
