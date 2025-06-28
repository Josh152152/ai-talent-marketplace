from sentence_transformers import SentenceTransformer, util

class MatchingSystem:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def find_matches(self, job_description, candidates_df, top_n=3):
        job_embedding = self.model.encode(job_description['job_requirements'], convert_to_tensor=True)

        candidates_df = candidates_df.dropna(subset=['profile_details'])  # Avoid empty profiles
        candidates_df['embedding'] = candidates_df['profile_details'].apply(
            lambda text: self.model.encode(text, convert_to_tensor=True)
        )

        candidates_df['similarity'] = candidates_df['embedding'].apply(
            lambda emb: util.cos_sim(emb, job_embedding).item()
        )

        top_matches = candidates_df.sort_values(by='similarity', ascending=False).head(top_n)
        return top_matches.to_dict(orient='records')
