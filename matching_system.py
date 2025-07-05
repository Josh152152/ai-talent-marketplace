class MatchingSystem:
    def __init__(self):
        pass

    def find_matches(self, job, candidates):
        # Normalize job skills
        job_skills = job.get("skills", "")
        if isinstance(job_skills, str):
            job_skills = set(s.strip().lower() for s in job_skills.split(",") if s.strip())
        elif isinstance(job_skills, list):
            job_skills = set(s.strip().lower() for s in job_skills if isinstance(s, str))
        else:
            job_skills = set()

        matches = []

        for candidate in candidates:
            # Normalize candidate skills
            candidate_skills_raw = candidate.get("Skills", "")
            if isinstance(candidate_skills_raw, str):
                candidate_skills = set(s.strip().lower() for s in candidate_skills_raw.split(",") if s.strip())
            elif isinstance(candidate_skills_raw, list):
                candidate_skills = set(s.strip().lower() for s in candidate_skills_raw if isinstance(s, str))
            else:
                candidate_skills = set()

            # Compute intersection (match score)
            score = len(job_skills & candidate_skills)

            if score > 0:
                matches.append({
                    "name": candidate.get("Name", "Unknown"),
                    "email": candidate.get("Email", "Unknown"),
                    "match_score": score
                })

        # Return sorted list of matches
        return sorted(matches, key=lambda x: x["match_score"], reverse=True)
