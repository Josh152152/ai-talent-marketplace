class MatchingSystem:
    def __init__(self):
        pass

    def normalize_skills(self, skill_list):
        return set(s.strip().lower() for s in skill_list if s.strip())

    def find_matches(self, job, candidates):
        job_skills = self.normalize_skills(job.get("skills", "").split(","))
        matches = []

        for candidate in candidates:
            candidate_skills = self.normalize_skills(candidate.get("skills", "").split(","))
            score = len(job_skills & candidate_skills)
            if score > 0:
                matches.append({
                    "name": candidate.get("name"),
                    "email": candidate.get("email"),
                    "match_score": score
                })

        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches
