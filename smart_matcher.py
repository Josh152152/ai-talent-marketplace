import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI

client = OpenAI()

def get_embedding(text, model="text-embedding-3-large"):
    try:
        print(f"DEBUG: Getting embedding for text: {repr(text)}")
        response = client.embeddings.create(
            model=model,
            input=text
        )
        embedding = response.data[0].embedding
        if not embedding:
            raise ValueError("Empty embedding returned.")
        return embedding
    except Exception as e:
        print(f"🔥 Error in get_embedding: {e}")
        return None

def match_jobs(candidate_text, job_summaries):
    cand_emb = get_embedding(candidate_text)
    if not cand_emb:
        return []

    cand_emb = np.array(cand_emb).reshape(1, -1)

    job_embeddings = []
    job_texts = []

    for job in job_summaries:
        summary = job.get("Job Summary", "")
        emb = get_embedding(summary)
        if emb:
            job_embeddings.append(emb)
            job_texts.append(job)

    if not job_embeddings:
        return []

    job_embeddings = np.array(job_embeddings)
    similarities = cosine_similarity(cand_emb, job_embeddings)[0]
    scored = list(zip(job_texts, similarities))
    scored.sort(key=lambda x: x[1], reverse=True)

    return scored[:5]

def suggest_missing_skills(candidate_skills, job_text):
    """
    Suggest up to 5 missing keywords that appear in job_text but not in candidate_skills.
    """
    job_keywords = set(word.lower() for word in job_text.split())
    cand_keywords = set(word.lower().strip() for word in candidate_skills.split(","))
    missing = job_keywords - cand_keywords
    return list(missing)[:5]
