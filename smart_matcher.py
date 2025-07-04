import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI

client = OpenAI()

def get_embedding(text, model="text-embedding-3-large"):
    if not text or not text.strip():
        return None
    try:
        response = client.embeddings.create(model=model, input=text.strip())
        return response.data[0].embedding
    except Exception as e:
        print(f"🔥 Embedding error for input: {text[:100]}... → {e}")
        return None

def match_jobs(candidate_text, job_rows):
    """
    Compare candidate text (summary + location) to jobs (summary + location).
    Each job should contain 'Job Summary' and 'Job Location' fields.
    Returns top 5 matches with cosine similarity scores.
    """
    # Include location in candidate input
    candidate_input = candidate_text.strip()
    candidate_location = ""
    if isinstance(candidate_text, dict):
        candidate_input = candidate_text.get("Summary", "").strip()
        candidate_location = candidate_text.get("Location", "").strip()
    full_candidate_input = f"{candidate_input} {candidate_location}".strip()

    cand_emb = get_embedding(full_candidate_input)
    if cand_emb is None:
        return []

    embeddings = []
    valid_jobs = []

    for job in job_rows:
        job_summary = job.get("Job Summary", "").strip()
        job_location = job.get("Job Location", "").strip()
        combined = f"{job_summary} {job_location}".strip()
        emb = get_embedding(combined)
        if emb:
            embeddings.append(emb)
            valid_jobs.append(job)

    if not embeddings:
        return []

    sim_scores = cosine_similarity([cand_emb], embeddings)[0]
    matches = list(zip(valid_jobs, sim_scores))
    matches.sort(key=lambda x: x[1], reverse=True)

    return matches[:5]

def suggest_missing_skills(candidate_skills, job_text):
    """
    Suggests skills that appear in the job text but are missing from candidate_skills.
    Returns a list of up to 5 missing keywords.
    """
    job_keywords = set(word.lower().strip(".,()") for word in job_text.split())
    cand_keywords = set(word.lower().strip() for word in candidate_skills.split(","))
    missing = job_keywords - cand_keywords
    return list(missing)[:5]
