class MatchingSystem:
    def find_matches(self, job, candidates):
        required_skills = job.get("required_skills", "").lower().split(",")
        matches = []

        for cand in candidates:
            candidate_skills = cand.get("skills", "").lower()
            if any(skill.strip() in candidate_skills for skill in required_skills):
                matches.append(cand)

        return matches
