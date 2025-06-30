# adzuna_api.py

import os
import requests

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
ADZUNA_COUNTRY = os.getenv("ADZUNA_COUNTRY", "us")

def query_jobs(keywords, location, max_results=20):
    base_url = f"https://api.adzuna.com/v1/api/jobs/{ADZUNA_COUNTRY}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": keywords,
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
