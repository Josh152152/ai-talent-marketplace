import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI

client = OpenAI()

def get_embedding(text, model="text-embedding-3-large"):
    if not text.strip():
        return None
    response = client.embeddings.create(model=model, input=text.strip())
    return response.data[0].embedding

def match_jobs(candidate_summary, job_rows):
    """
    Compare candidate summary to job summaries from job_rows.
    Returns top 5 matches with similarity scores.
    """
    cand_emb = get_embedding(candidate_summary)
    if cand_emb is None:
        return []

    embeddings = []
    valid_jobs = []

    for job in job_rows:
        job_text = job.get("Job Summary", "")
        if job_text.strip():
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
    job_keywords = set(word.lower() for word in job_text.split())
    cand_keywords = set(word.lower().strip() for word in candidate_skills.split(","))
    missing = job_keywords - cand_keywords
    return list(missing)[:5]
