import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI

# Initialize OpenAI client once using your API key from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text, model="text-embedding-3-large"):
    """
    Converts a given text string to a dense vector embedding using OpenAI.
    """
    print(f"DEBUG: Getting embedding for text: {repr(text)}")
    response = client.embeddings.create(
        model=model,
        input=text
    )
    return response.data[0].embedding

def match_jobs(candidate_text, job_texts):
    """
    Compute cosine similarity between a candidate summary and job summaries.
    Returns top 5 matches.
    """
    try:
        cand_emb = get_embedding(candidate_text)
        job_embeddings = [get_embedding(job['Job Summary']) if isinstance(job, dict) else get_embedding(job)
                          for job in job_texts]

        similarities = cosine_similarity([cand_emb], job_embeddings)[0]
        scored = list(zip(job_texts, similarities))
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[:5]  # Top 5 matches
    except Exception as e:
        print(f"🔥 Error in match_jobs: {e}")
        return []

def suggest_missing_skills(candidate_skills, job_text):
    """
    Suggest skills from job text that are not already in candidate skills.
    Returns up to 5 suggestions.
    """
    job_keywords = set(word.lower() for word in job_text.split())
    cand_keywords = set(word.lower().strip() for word in candidate_skills.split(","))
    missing = job_keywords - cand_keywords
    return list(missing)[:5]
