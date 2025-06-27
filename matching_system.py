from sentence_transformers import SentenceTransformer, util
import pandas as pd

class MatchingSystem:
    def __init__(self):
        # Load sentence transformer model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def preprocess_text(self, text):
        return str(text).strip().lower() if text else ""

    def extract_features(self, row):
        # Concatenate key candidate features into one string
        fields = [
            row.get('current_position', ''),
            row.get('skills', ''),
            row.get('education', ''),
            row.get('profile_summary', ''),
            row.get('languages', ''),
            row.get('achievements', '')
        ]
        return " ".join([self.preprocess_text(f) for f in fields])

    def find_matches(self, job_data, candidates_df, top_k=5):
        job_text = f"{job_data.get('job_title', '')} {job_data.get('job_description', '')} {job_data.get('required_skills', '')}"
        job_embedding = self.model.encode(self.preprocess_text(job_text), convert_to_tensor=True)

        matches = []
        for _, row in candidates_df.iterrows():
            candidate_text = self.extract_features(row)
            candidate_embedding = self.model.encode(candidate_text, convert_to_tensor=True)

            similarity_score = util.pytorch_cos_sim(job_embedding, candidate_embedding).item()

            match_info = row.to_dict()
            match_info['match_score'] = round(similarity_score, 4)
            matches.append(match_info)

        # Sort by match score, descending
        matches_sorted = sorted(matches, key=lambda x: x['match_score'], reverse=True)

        return matches_sorted[:top_k]
