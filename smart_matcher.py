import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI

# Initialize OpenAI client once
client = OpenAI()

def get_embedding(text, model="text-embedding-3-large"):
    """
    Get embedding vector from OpenAI using the new API.
    """
    response = client.embeddings.create(
        input=text,
        model=model  # use the argument passed or default
    )
    return response.data[0].embedding

def match_jobs(candidate_text, job_titles):
    """
    Compare candidate profile text to job titles, return top 5 matches by cosine similarity.
    """
    cand_emb = get_embedding(candidate_text)
    job_embeddings = [get_embedding(title) for title in job_titles]

    similarities = cosine_similarity([cand_emb], job_embeddings)[0]
    scored = list(zip(job_titles, similarities))
    scored.sort(key=lambda x: x[1], reverse=True)

    return scored[:5]  # Top 5 matches

def suggest_missing_skills(candidate_skills, job_text):
    """
    Suggest up to 5 missing keywords that appear in job_text but not in candidate_skills.
    """
    job_keywords = set(word.lower() for word in job_text.split())
    cand_keywords = set(word.lower().strip() for word in candidate_skills.split(","))
    missing = job_keywords - cand_keywords
    return list(missing)[:5]
