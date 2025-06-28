class MatchingSystem:
    def __init__(self):
        pass

    def find_matches(self, job, candidates):
        job_skills = set(job.get("skills", []))
        matches = []

        for candidate in candidates:
            candidate_skills = set(candidate.get("skills", "").split(","))
            score = len(job_skills & candidate_skills)
            if score > 0:
                matches.append({
                    "name": candidate.get("name"),
                    "email": candidate.get("email"),
                    "match_score": score
                })

        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches
