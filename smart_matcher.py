import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from math import exp

client = OpenAI()
geolocator = Nominatim(user_agent="job-matcher")

def get_embedding(text, model="text-embedding-3-large"):
    if not text or not text.strip():
        return None
    try:
        response = client.embeddings.create(model=model, input=text.strip())
        return response.data[0].embedding
    except Exception as e:
        print(f"🔥 Embedding error for input: {text[:100]}... → {e}")
        return None

def get_latlon(location):
    try:
        if not location:
            return None
        loc = geolocator.geocode(location)
        if loc:
            return (loc.latitude, loc.longitude)
    except Exception as e:
        print(f"⚠️ Geolocation error for '{location}': {e}")
    return None

def compute_distance_km(loc1, loc2):
    if not loc1 or not loc2:
        return None
    try:
        return geodesic(loc1, loc2).km
    except:
        return None

def location_penalty(distance_km):
    if distance_km is None:
        return 1.0
    return exp(-distance_km / 2000)  # tweakable

def match_jobs(candidate_record, job_rows):
    candidate_summary = candidate_record.get("Summary", "").strip()
    candidate_location = candidate_record.get("Location", "").strip()
    full_candidate_text = f"{candidate_summary}. Location: {candidate_location}"
    cand_emb = get_embedding(full_candidate_text)
    cand_latlon = get_latlon(candidate_location)

    if cand_emb is None:
        return []

    embeddings = []
    valid_jobs = []

    for job in job_rows:
        job_summary = job.get("Job Summary", "").strip()
        job_location = job.get("Job Location", "").strip()
        full_job_text = f"{job_summary}. Location: {job_location}"
        emb = get_embedding(full_job_text)
        job_latlon = get_latlon(job_location)

        if emb:
            embeddings.append((emb, job, job_latlon))

    if not embeddings:
        return []

    results = []
    for emb, job, job_latlon in embeddings:
        sim = cosine_similarity([cand_emb], [emb])[0][0]
        dist_km = compute_distance_km(cand_latlon, job_latlon)
        penalty = location_penalty(dist_km)
        adjusted = sim * penalty
        job["Distance (km)"] = round(dist_km or 0, 1)
        results.append((job, adjusted, sim))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:5]

def suggest_missing_skills(candidate_skills, job_text):
    job_keywords = set(word.lower().strip(".,()") for word in job_text.split())
    cand_keywords = set(word.lower().strip() for word in candidate_skills.split(","))
    missing = job_keywords - cand_keywords
    return list(missing)[:5]
