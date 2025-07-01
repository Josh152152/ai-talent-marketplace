from flask import Flask, request, jsonify, session, redirect, render_template
from flask_cors import CORS
from functools import wraps
import os
import sys
import bcrypt
from dotenv import load_dotenv
from itsdangerous import URLSafeSerializer
from sheets import get_gspread_client
from candidate_registration import CandidateRegistrationSystem
from matching_system import MatchingSystem
from smart_matcher import match_jobs, suggest_missing_skills  # embedding-based matcher

# Import query_jobs from your renamed helper, e.g. adzuna_helper.py (avoid circular import)
from adzuna_helper import query_jobs  # <-- rename your adzuna_api.py to adzuna_helper.py

sys.stdout.reconfigure(line_buffering=True)
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("APP_SECRET_KEY", "super-secret-key")

registration = CandidateRegistrationSystem()
matcher = MatchingSystem()

serializer = URLSafeSerializer(os.getenv("APP_SECRET_KEY", "default-secret"))

# Authentication and other routes here...

# ------------------- ADZUNA MATCH (AI) -------------------

@app.route("/adzuna_match", methods=["POST"])
def adzuna_match():
    try:
        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"error": "Email is required"}), 400

        client = get_gspread_client()
        sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
        records = sheet.get_all_records()

        candidate = next((r for r in records if r["Email"] == email), None)
        if not candidate:
            return jsonify({"error": "Candidate not found"}), 404

        location = candidate.get("Location", "")
        skills = candidate.get("Skills", "")
        summary = candidate.get("Summary", "")
        keywords = f"{skills} {summary}".strip()

        # Query Adzuna API for jobs
        adzuna_result = query_jobs(keywords=keywords, location=location)
        # adzuna_result['examples'] is a list of dicts {title, url}

        job_titles = [job["title"] for job in adzuna_result.get("examples", [])]

        if not job_titles:
            return jsonify({
                "matches_found": 0,
                "location": location,
                "top_matches": [],
                "missing_skills": [],
                "message": "No matching jobs found."
            })

        # Use embedding-based matcher on candidate's full keywords and job titles
        top_matches = match_jobs(keywords, job_titles)
        match_titles = [title for title, score in top_matches]
        top_job_text = match_titles[0] if match_titles else ""
        missing_skills = suggest_missing_skills(skills, top_job_text)

        return jsonify({
            "matches_found": len(match_titles),
            "top_matches": match_titles,
            "location": location,
            "missing_skills": missing_skills
        })

    except Exception as e:
        print(f"🔥 Error in /adzuna_match (AI): {e}")
        return jsonify({"error": str(e)}), 500

# ...other routes...

# At the bottom, run your app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
