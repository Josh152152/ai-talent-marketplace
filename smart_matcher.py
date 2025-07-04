import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

client = OpenAI()
geolocator = Nominatim(user_agent="ai-talent-matching")

def get_embedding(text, model="text-embedding-3-large"):
    if not text or not text.strip():
        return None
    try:
        response = client.embeddings.create(model=model, input=text.strip())
        return response.data[0].embedding
    except Exception as e:
        print(f"🔥 Embedding error: {text[:80]}... → {e}")
        return None

def get_coordinates(location_name):
    if not location_name:
        return None
    try:
        location = geolocator.geocode(location_name, timeout=10)
        if location:
            return (location.latitude, location.longitude)
    except Exception as e:
        print(f"🌍 Geocoding error for {location_name}: {e}")
    return None

def compute_geo_penalty(loc1, loc2):
    """
    Returns a penalty factor (0–1). 
    The farther the distance, the lower the factor.
    Max penalty at ~20,000 km → 50% similarity reduction.
    """
    coords1 = get_coordinates(loc1)
    coords2 = get_coordinates(loc2)

    if not coords1 or not coords2:
        return 1.0, None  # No penalty if unknown

    distance_km = geodesic(coords1, coords2).km
    penalty_factor = max(0.5, 1 - (distance_km / 20000))
    return penalty_factor, distance_km

def match_jobs(candidate_record, job_rows):
    summary = candidate_record.get("Summary", "").strip()
    location = candidate_record.get("Location", "").strip()
    full_text = f"{summary}. Location: {location}"
    cand_emb = get_embedding(full_text)

    if cand_emb is None:
        return []

    embeddings = []
    valid_jobs = []
    geo_data = []

    for job in job_rows:
        job_summary = job.get("Job Summary", "").strip()
        job_location = job.get("Job Location", "").strip()
        job_text = f"{job_summary}. Location: {job_location}"
        emb = get_embedding(job_text)

        if emb:
            embeddings.append(emb)
            valid_jobs.append(job)

            penalty, distance_km = compute_geo_penalty(location, job_location)
            geo_data.append((penalty, distance_km))

    if not embeddings:
        return []

    sim_scores = cosine_similarity([cand_emb], embeddings)[0]
    matches = []

    for idx, job in enumerate(valid_jobs):
        sim = sim_scores[idx]
        penalty, distance_km = geo_data[idx]
        adjusted = sim * penalty
        matches.append({
            "summary": job.get("Job Summary", ""),
            "location": job.get("Job Location", ""),
            "score": round(float(adjusted), 4),
            "geo_penalty": round(penalty, 4),
            "geo_distance_km": round(distance_km, 2) if distance_km is not None else None,
            "reason": ", ".join(set(word.lower().strip(".,()") for word in summary.split()) &
                                set(word.lower().strip(".,()") for word in job.get("Job Summary", "").split()))
                     or "Semantic and location match"
        })

    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:5]

def suggest_missing_skills(candidate_skills, job_text):
    job_keywords = set(word.lower().strip(".,()") for word in job_text.split())
    cand_keywords = set(word.lower().strip() for word in candidate_skills.split(","))
    missing = job_keywords - cand_keywords
    return list(missing)[:5]
