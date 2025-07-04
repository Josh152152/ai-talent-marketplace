import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

client = OpenAI()
geolocator = Nominatim(user_agent="geo-matcher")

def get_embedding(text, model="text-embedding-3-large"):
    if not text or not text.strip():
        return None
    try:
        response = client.embeddings.create(model=model, input=text.strip())
        return response.data[0].embedding
    except Exception as e:
        print(f"\U0001F525 Embedding error for input: {text[:100]}... → {e}")
        return None

def get_coordinates(location):
    if not location.strip():
        return None
    try:
        loc = geolocator.geocode(location)
        return (loc.latitude, loc.longitude) if loc else None
    except Exception as e:
        print(f"\U0001F525 Geolocation error for: {location} → {e}")
        return None

def compute_distance_km(loc1, loc2):
    try:
        return geodesic(loc1, loc2).km
    except:
        return None

def match_jobs(candidate_record, job_rows):
    """
    Compare candidate (summary + location) to each job (summary + location).
    Adjust score based on geographic distance.
    Returns top 5 job matches.
    """
    candidate_summary = candidate_record.get("Summary", "").strip()
    candidate_location = candidate_record.get("Location", "").strip()
    full_candidate_text = f"{candidate_summary}. Location: {candidate_location}"
    
    cand_coords = get_coordinates(candidate_location)
    cand_emb = get_embedding(full_candidate_text)
    if cand_emb is None:
        return []

    matches = []
    for job in job_rows:
        job_summary = job.get("Job Summary", "").strip()
        job_location = job.get("Job Location", "").strip()
        full_job_text = f"{job_summary}. Location: {job_location}"

        job_emb = get_embedding(full_job_text)
        if job_emb is None:
            continue

        raw_score = cosine_similarity([cand_emb], [job_emb])[0][0]
        job_coords = get_coordinates(job_location)

        distance_km = compute_distance_km(cand_coords, job_coords) if cand_coords and job_coords else None

        # Adjust score by distance penalty
        if distance_km is not None:
            # Distance penalty (example: 1% penalty per 100km)
            distance_penalty = 0.01 * (distance_km / 100)
            adjusted_score = raw_score * (1 - min(distance_penalty, 0.5))  # cap penalty at 50%
        else:
            adjusted_score = raw_score  # no adjustment if unknown

        job["Distance (km)"] = round(distance_km, 1) if distance_km else None
        matches.append((job, adjusted_score, raw_score))

    matches.sort(key=lambda x: x[1], reverse=True)
    return matches[:5]

def suggest_missing_skills(candidate_skills, job_text):
    """
    Identify missing keywords in job description not present in candidate's skills.
    """
    job_keywords = set(word.lower().strip(".,()") for word in job_text.split())
    cand_keywords = set(word.lower().strip() for word in candidate_skills.split(","))
    missing = job_keywords - cand_keywords
    return list(missing)[:5]
