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
        location = geolocator.geocode(location_name)
        if location:
            return (location.latitude, location.longitude)
    except Exception as e:
        print(f"🌍 Geocoding error for {location_name}: {e}")
    return None

def compute_geo_penalty(loc1, loc2):
    """
    Returns a penalty factor (0–1). 
    The farther the distance, the lower the factor.
    Max penalty at ~10,000 km → 50% similarity reduction.
    """
    coords1 = get_coordinates(loc1)
    coords2 = get_coordinates(loc2)

    if not coords1 or not coords2:
        return 1.0  # no penalty if location unknown

    distance_km = geodesic(coords1, coords2).km
    penalty_factor = max(0.5, 1 - (distance_km / 20000))  # max 50% penalty
    return penalty_factor

def match_jobs(candidate_record, job_rows):
    """
    Returns top 5 jobs matched to the candidate using semantic similarity and location penalty.
    """
    summary = candidate_record.get("Summary", "").strip()
    location = candidate_record.get("Location", "").strip()
    full_text = f"{summary}. Location: {location}"
    cand_emb = get_embedding(full_text)

    if cand_emb is None:
        return []

    embeddings = []
    valid_jobs = []
    geo_factors = []

    for job in job_rows:
        job_summary = job.get("Job Summary", "").strip()
        job_location = job.get("Job Location", "").strip()
        job_text = f"{job_summary}. Location: {job_location}"
        emb = get_embedding(job_text)

        if emb:
            embeddings.append(emb)
            valid_jobs.append(job)
            geo_factors.append(compute_geo_penalty(location, job_location))

    if not embeddings:
        return []

    sim_scores = cosine_similarity([cand_emb], embeddings)[0]
    adjusted_scores = [sim * geo for sim, geo in zip(sim_scores, geo_factors)]
    matches = list(zip(valid_jobs, adjusted_scores))
    matches.sort(key=lambda x: x[1], reverse=True)

    return matches[:5]

def suggest_missing_skills(candidate_skills, job_text):
    job_keywords = set(word.lower().strip(".,()") for word in job_text.split())
    cand_keywords = set(word.lower().strip() for word in candidate_skills.split(","))
    missing = job_keywords - cand_keywords
    return list(missing)[:5]
