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
    Compare candidate text to job descriptions with location context.
    Expects each job dict to include 'embedding_input' key.
    Returns top 5 matches with cosine similarity scores.
    """
    cand_emb = get_embedding(candidate_text)
    if cand_emb is None:
        return []

    embeddings = []
    valid_jobs = []

    for job in job_rows:
        job_text = job.get("embedding_input") or job.get("Job Summary")
        emb = get_embedding(job_text)
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
    Extract words from job text not already in candidate_skills.
    Returns up to 5 missing keywords (case-insensitive).
    """
    job_keywords = set(word.lower().strip(".,()") for word in job_text.split())
    cand_keywords = set(word.lower().strip() for word in candidate_skills.split(","))
    missing = job_keywords - cand_keywords
    return list(missing)[:5]
