class MatchingSystem:
    def __init__(self):
        pass

    def find_matches(self, job, candidates):
        # Job skills processing: split by commas and clean up extra spaces
        job_skills = job.get("skills", "")
        if isinstance(job_skills, str):  # If it's a string, split by commas
            job_skills = set([s.strip().lower() for s in job_skills.split(",")])
        else:  # If it's already a list, directly process it
            job_skills = set([s.strip().lower() for s in job_skills])

        print(f"Job Skills: {job_skills}")  # Log job skills to see if they are split and cleaned properly
        
        matches = []

        # Loop through the candidates
        for candidate in candidates:
            # Candidate skills processing: split by commas and clean up extra spaces
            candidate_skills_raw = candidate.get("Skills", "")  # Access the 'Skills' column in Google Sheets
            if isinstance(candidate_skills_raw, str):  # If it's a string, split by commas
                candidate_skills = set([s.strip().lower() for s in candidate_skills_raw.split(",")])
            else:  # If it's already a list, directly process it
                candidate_skills = set([s.strip().lower() for s in candidate_skills_raw])

            print(f"Candidate Skills for {candidate['Name']}: {candidate_skills}")  # Log candidate skills

            # Calculate match score: intersection of job skills and candidate skills
            score = len(job_skills & candidate_skills)  # Match score is based on overlapping skills
            print(f"Matching Score: {score}")  # Log match score for debugging

            if score > 0:  # Only consider matches with a non-zero score
                matches.append({
                    "name": candidate.get("Name", "No Name Provided"),  # Use 'Name' column in Google Sheets
                    "email": candidate.get("Email", "No Email Provided"),  # Use 'Email' column in Google Sheets
                    "match_score": score
                })

        # Sort matches by score in descending order (highest match first)
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches
