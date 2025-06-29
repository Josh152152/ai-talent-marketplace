class MatchingSystem:
    def __init__(self):
        pass

    def find_matches(self, job, candidates):
        # Check if job skills is a list, if not, split by commas
        job_skills = job.get("skills", "")
        if isinstance(job_skills, str):  # If it's a string, split it
            job_skills = set([s.strip().lower() for s in job_skills.split(",")])
        else:  # If it's already a list, directly process it
            job_skills = set([s.strip().lower() for s in job_skills])

        print(f"Job Skills: {job_skills}")  # Log job skills to see if they are split and cleaned properly
        
        matches = []

        for candidate in candidates:
            # Check if candidate skills is a list, if not, split by commas
            candidate_skills_raw = candidate.get("skills", "")
            if isinstance(candidate_skills_raw, str):  # If it's a string, split it
                candidate_skills = set([s.strip().lower() for s in candidate_skills_raw.split(",")])
            else:  # If it's already a list, directly process it
                candidate_skills = set([s.strip().lower() for s in candidate_skills_raw])

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
