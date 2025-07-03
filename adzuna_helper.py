import os
import requests
import re

# Load Adzuna credentials from environment
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

# Manual mapping of known keywords to job roles
KEYWORD_TO_ROLE = {
    "html": "frontend developer",
    "css": "frontend developer",
    "javascript": "frontend developer",
    "react": "frontend developer",
    "python": "software engineer",
    "django": "python developer",
    "flask": "python developer",
    "sql": "data analyst",
    "excel": "data analyst",
    "aws": "cloud engineer",
    "node": "backend developer",
    "java": "backend developer",
    "api": "backend developer",
    "dcs": "control systems engineer",
    "plc": "automation engineer",
    "scada": "automation engineer",
    "refinery": "chemical engineer",
    "automation": "automation engineer",
    "process": "process engineer"
}

# Extract clean keywords from text
def clean_keywords(text):
    if not text:
        return []
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return list(set(re.findall(r"\b\w{3,}\b", text)))

# Map cleaned keywords to known job roles
def map_keywords_to_roles(keywords):
    return list(set(KEYWORD_TO_ROLE[k] for k in keywords if k in KEYWORD_TO_ROLE))

# Infer country from location
def detect_country(location):
    if not location:
        return "gb"
    loc = location.lower()
    us_cities = ["new york", "san francisco", "los angeles", "chicago", "seattle", "boston", "austin", "washington"]
    if any(city in loc for city in us_cities) or "united states" in loc or "usa" in loc:
        return "us"
    return "gb"

# Query Adzuna API for job listings
def query_jobs(keywords, location="London", max_results=10):
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        return {"error": "Missing Adzuna credentials"}

    country_code = detect_country(location)
    keyword_list = clean_keywords(keywords)
    role_terms = map_keywords_to_roles(keyword_list)
    search_terms = " ".join(role_terms[:3]) if role_terms else " ".join(keyword_list[:5])

    url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": search_terms,
        "where": location,
        "results_per_page": max_results,
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return {
                "count": data.get("count", 0),
                "examples": [
                    {
                        "title": job.get("title"),
                        "description": job.get("description", ""),
                        "url": job.get("redirect_url", "")
                    }
                    for job in data.get("results", [])
                ]
            }
        else:
            return {
                "error": "Adzuna API request failed",
                "status": response.status_code,
                "details": response.text
            }
    except Exception as e:
        return {"error": str(e)}

# Suggest additional skills to unlock more jobs
def suggest_skill_expansion(current_skills, location, max_skills=3):
    base_result = query_jobs(keywords=" ".join(current_skills), location=location, max_results=50)
    if "examples" not in base_result or not base_result["examples"]:
        return []

    all_descriptions = []
    for job in base_result["examples"]:
        text = f"{job.get('title', '')} {job.get('description', '')}"
        all_descriptions.append(text.lower())

    combined_text = " ".join(all_descriptions)
    all_words = clean_keywords(combined_text)
    skill_candidates = [word for word in all_words if word not in current_skills]

    freq = {}
    for word in skill_candidates:
        freq[word] = freq.get(word, 0) + 1

    sorted_skills = sorted(freq.items(), key=lambda x: x[1], reverse=True)

    suggestions = []
    for skill, _ in sorted_skills[:10]:
        simulated = query_jobs(keywords=" ".join(current_skills + [skill]), location=location, max_results=50)
        extra_jobs = max(0, simulated.get("count", 0) - base_result.get("count", 0))
        if extra_jobs > 0:
            suggestions.append({
                "skill": skill,
                "extra_jobs_unlocked": extra_jobs
            })

    return sorted(suggestions, key=lambda x: x["extra_jobs_unlocked"], reverse=True)[:max_skills]
