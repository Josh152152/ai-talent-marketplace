class MatchingSystem:
    def __init__(self):
        pass

    def normalize_skills(self, skills_raw):
        if isinstance(skills_raw, str):
            return set(skill.strip().lower() for skill in skills_raw.split(",") if skill.strip())
        elif isinstance(skills_raw, list):
            return set(skill.strip().lower() for skill in skills_raw if isinstance(skill, str))
        return set()

    def find_matches(self, job, candidates):
        job_skills = self.normalize_skills(job.get("skills", ""))
        matches = []

        for candidate in candidates:
            candidate_skills = self.normalize_skills(candidate.get("skills", ""))
            score = len(job_skills & candidate_skills)

            if score > 0:
                matches.append({
                    "name": candidate.get("name"),
                    "email": candidate.get("email"),
                    "match_score": score
                })

        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches
