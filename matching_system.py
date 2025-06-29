class MatchingSystem:
    def __init__(self):
        pass

    def find_matches(self, job, candidates):
        # Process job skills
        job_skills = job.get("skills", "")
        if isinstance(job_skills, str):  # If it's a string, split it
            job_skills = set([s.strip().lower() for s in job_skills.split(",")])
        else:  # If it's already a list, directly process it
            job_skills = set([s.strip().lower() for s in job_skills])

        print(f"Job Skills: {job_skills}")  # Log job skills
        
        matches = []

        for candidate in candidates:
            # Process candidate skills
            candidate_skills_raw = candidate.get("Skills", "")  # Update to match the correct column name (Skills)
            if isinstance(candidate_skills_raw, str):  # If it's a string, split it
                candidate_skills = set([s.strip().lower() for s in candidate_skills_raw.split(",")])
            else:  # If it's already a list, directly process it
                candidate_skills = set([s.strip().lower() for s in candidate_skills_raw])

            print(f"Candidate Skills for {candidate['Name']}: {candidate_skills}")  # Log candidate skills

            # Calculate match score
            score = len(job_skills & candidate_skills)
            print(f"Matching Score: {score}")  # Log match score

            # Ensure 'Name' is being used correctly (name column in Google Sheets)
            if score > 0:
                matches.append({
                    "name": candidate.get("Name", "No Name Provided"),  # Use 'Name' instead of 'candName'
                    "email": candidate.get("Email", "No Email Provided"),  # Use 'Email' instead of 'candEmail'
                    "match_score": score
                })

        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches
