class MatchingSystem:
    def __init__(self):
        pass

    def find_matches(self, job, candidates):
        # Log the job skills to ensure it's being split and processed correctly
        job_skills = set([s.strip().lower() for s in job.get("skills", "").split(",")])
        print(f"Job Skills: {job_skills}")  # This logs the job skills to the console

        matches = []

        for candidate in candidates:
            # Log the candidate skills to ensure it's being split and processed correctly
            candidate_skills_raw = candidate.get("skills", "")
            candidate_skills = set([s.strip().lower() for s in candidate_skills_raw.split(",")])
            print(f"Candidate Skills for {candidate['name']}: {candidate_skills}")  # This logs candidate skills to the console

            # Calculate the matching score
            score = len(job_skills & candidate_skills)  # Intersection of job and candidate skills

            # If there's a match, append the result
            if score > 0:
                matches.append({
                    "name": candidate.get("name"),
                    "email": candidate.get("email"),
                    "match_score": score
                })

        # Sort matches by score in descending order
        matches.sort(key=lambda x: x["match_score"], reverse=True)

        return matches

