class MatchingSystem:
    def __init__(self):
        pass

    def find_matches(self, job, candidates):
        job_skills_raw = job.get("skills", "")
        job_skills = set(s.strip().lower() for s in job_skills_raw.split(",") if s.strip())
        matches = []

        for candidate in candidates:
            candidate_skills_raw = candidate.get("skills", "")
            candidate_skills = set(s.strip().lower() for s in candidate_skills_raw.split(",") if s.strip())
            score = len(job_skills & candidate_skills)

            if score > 0:
                matches.append({
                    "name": candidate.get("name"),
                    "email": candidate.get("email"),
                    "match_score": score
                })

        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches
