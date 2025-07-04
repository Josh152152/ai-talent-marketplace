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

def match_jobs(candidate_record, job_rows):
    """
    Compare candidate (summary + location) to each job (summary + location).
    Returns top 5 job matches by cosine similarity.
    """
    candidate_summary = candidate_record.get("Summary", "").strip()
    candidate_location = candidate_record.get("Location", "").strip()
    full_candidate_text = f"{candidate_summary}. Location: {candidate_location}"

    cand_emb = get_embedding(full_candidate_text)
    if cand_emb is None:
        return []

    embeddings = []
    valid_jobs = []

    for job in job_rows:
        job_summary = job.get("Job Summary", "").strip()
        job_location = job.get("Job Location", "").strip()
        full_job_text = f"{job_summary}. Location: {job_location}"

        emb = get_embedding(full_job_text)
        if emb:
            embeddings.append(emb)
            valid_jobs.append({
                **job,
                "embedding_input": full_job_text,
                "location": job_location
            })

    if not embeddings:
        return []

    sim_scores = cosine_similarity([cand_emb], embeddings)[0]
    matches = list(zip(valid_jobs, sim_scores))
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
