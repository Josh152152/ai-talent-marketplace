class MatchingSystem:
    def __init__(self):
        pass

    def find_matches(self, job, candidates):
        job_skills = set(skill.strip().lower() for skill in job.get("skills", "").split(","))
        matches = []

        for candidate in candidates:
            # Try 'skills' field first, then fall back to 'profile_details'
            raw_skills = candidate.get("skills") or candidate.get("profile_details") or ""
            candidate_skills = set(skill.strip().lower() for skill in raw_skills.split(","))

            score = len(job_skills & candidate_skills)
            if score > 0:
                matches.append({
                    "name": candidate.get("name"),
                    "email": candidate.get("email"),
                    "match_score": score
                })

        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches
