import os
import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
import math

client = OpenAI()

# === 1. EMBEDDING ===

def get_embedding(text, model="text-embedding-3-large"):
    if not text or not text.strip():
        return None
    try:
        response = client.embeddings.create(model=model, input=text.strip())
        return response.data[0].embedding
    except Exception as e:
        print(f"🔥 Embedding error for input: {text[:100]}... → {e}")
        return None

# === 2. GEOCODING USING OPENSTREETMAP ===

def geocode(location):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": location,
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "AI-Talent-Matcher/1.0"
        }
        res = requests.get(url, params=params, headers=headers)
        data = res.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return (lat, lon)
        return None
    except Exception as e:
        print(f"⚠️ Geocoding failed for '{location}': {e}")
        return None

# === 3. DISTANCE CALCULATION ===

def haversine(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371  # Earth radius in km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# === 4. DISTANCE-BASED SCORE PENALIZATION ===

def apply_distance_penalty(sim_score, distance_km, max_penalty=0.2):
    penalty = min(distance_km / 10000, max_penalty)  # e.g. 10,000 km maxes penalty
    return round(sim_score * (1 - penalty), 4)

# === 5. MAIN MATCHING FUNCTION ===

def match_jobs(candidate_record, job_rows):
    candidate_summary = candidate_record.get("Summary", "").strip()
    candidate_location = candidate_record.get("Location", "").strip()
    full_candidate_text = f"{candidate_summary}. Location: {candidate_location}"

    cand_emb = get_embedding(full_candidate_text)
    cand_coord = geocode(candidate_location)

    if cand_emb is None:
        return []

    matches = []
    for job in job_rows:
        job_summary = job.get("Job Summary", "").strip()
        job_location = job.get("Location", "").strip()
        full_job_text = f"{job_summary}. Location: {job_location}"
        job_emb = get_embedding(full_job_text)
        job_coord = geocode(job_location)

        if job_emb:
            raw_score = cosine_similarity([cand_emb], [job_emb])[0][0]
            distance_km = haversine(cand_coord, job_coord) if cand_coord and job_coord else None
            adjusted = apply_distance_penalty(raw_score, distance_km) if distance_km else raw_score

            matches.append({
                "summary": job_summary,
                "location": job_location,
                "raw_score": round(float(raw_score), 4),
                "distance_km": round(distance_km, 1) if distance_km else None,
                "score": adjusted
            })

    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:5]

# === 6. MISSING SKILLS SUGGESTION ===

def suggest_missing_skills(candidate_skills, job_text):
    job_keywords = set(word.lower().strip(".,()") for word in job_text.split())
    cand_keywords = set(word.lower().strip() for word in candidate_skills.split(","))
    missing = job_keywords - cand_keywords
    return list(missing)[:5]
