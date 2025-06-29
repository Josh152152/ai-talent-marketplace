class MatchingSystem:
    def __init__(self):
        pass

    def find_matches(self, job, candidates):
        # Job skills processing (split by commas)
        job_skills = set([s.strip().lower() for s in job.get("skills", "").split(",")])
        print(f"Job Skills: {job_skills}")  # Log job skills to see if they are split and cleaned properly
        
        matches = []

        for candidate in candidates:
            # Candidate skills processing
            candidate_skills_raw = candidate.get("skills", "")
            candidate_skills = set([s.strip().lower() for s in candidate_skills_raw.split(",")])
            print(f"Candidate Skills for {candidate['name']}: {candidate_skills}")  # Log candidate skills

            # Calculate match score based on intersection of job skills and candidate skills
            score = len(job_skills & candidate_skills)
            print(f"Matching Score: {score}")  # Log match score for debugging

            if score > 0:
                matches.append({
                    "name": candidate.get("name"),
                    "email": candidate.get("email"),
                    "match_score": score
                })

        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches
