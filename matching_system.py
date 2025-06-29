class MatchingSystem:
    def __init__(self):
        pass

    def find_matches(self, job, candidates):
        # Job skills processing
        job_skills = set([s.strip().lower() for s in job.get("skills", "").split(",")])  # Added split
        matches = []

        for candidate in candidates:
            # Candidate skills processing
            candidate_skills_raw = candidate.get("skills", "")
            candidate_skills = set([s.strip().lower() for s in candidate_skills_raw.split(",")])  # Split and strip spaces

            # Matching score based on intersection
            score = len(job_skills & candidate_skills)

            if score > 0:
                matches.append({
                    "name": candidate.get("name"),
                    "email": candidate.get("email"),
                    "match_score": score
                })

        # Sort matches by the highest match score
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches

