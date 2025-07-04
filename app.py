from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
import os
import sys
from dotenv import load_dotenv
from sheets import get_gspread_client
from candidate_registration import CandidateRegistrationSystem
from matching_system import MatchingSystem
from adzuna_helper import query_jobs, detect_country
from smart_matcher import suggest_missing_skills, match_jobs

sys.stdout.reconfigure(line_buffering=True)
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("APP_SECRET_KEY", "super-secret-key")

registration = CandidateRegistrationSystem()
matcher = MatchingSystem()

# ------------------- HEALTH -------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200

# ------------------- DASHBOARD -------------------

@app.route("/dashboard", methods=["GET"])
def candidate_dashboard():
    try:
        email = request.args.get("email")
        if not email:
            return "Missing email", 400

        client = get_gspread_client()
        sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
        records = sheet.get_all_records()

        for row in records:
            if row.get("Email") == email:
                return render_template("candidate_dashboard.html", data=row)

        return render_template("candidate_dashboard.html", data={"Email": email, "Skills": "Not set yet"})
    except Exception as e:
        print(f"🔥 Error in /dashboard: {e}")
        return "Dashboard error", 500

@app.route("/update_skills", methods=["POST"])
def update_skills():
    try:
        email = request.form.get("email")
        new_skills = request.form.get("skills", "")
        if not email:
            return "Missing email", 400

        client = get_gspread_client()
        sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
        records = sheet.get_all_records()

        for i, row in enumerate(records):
            if row.get("Email") == email:
                sheet.update_cell(i + 2, 3, new_skills)
                return redirect(f"/dashboard?email={email}")

        return "Candidate not found.", 404
    except Exception as e:
        print(f"🔥 Error in /update_skills: {e}")
        return "Internal server error", 500

# ------------------- SUGGEST SKILLS -------------------

@app.route("/suggest_skills", methods=["POST"])
def suggest_skills():
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

        skills = [s.strip().lower() for s in candidate.get("Skills", "").split(",") if s.strip()]
        location = candidate.get("Location", "")

        from adzuna_helper import suggest_skill_expansion
        suggestions = suggest_skill_expansion(skills, location)

        return jsonify({"email": email, "suggested_skills": suggestions})
    except Exception as e:
        print(f"🔥 Error in /suggest_skills: {e}")
        return jsonify({"error": str(e)}), 500

# ------------------- JOB SEARCH -------------------

@app.route("/debug_jobs", methods=["POST"])
def debug_jobs():
    try:
        data = request.get_json()
        email = data.get("email")
        if not email:
            return jsonify({"error": "Missing email"}), 400

        client = get_gspread_client()
        sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
        records = sheet.get_all_records()

        candidate = next((r for r in records if r["Email"] == email), None)
        if not candidate:
            return jsonify({"error": "Candidate not found"}), 404

        skills = candidate.get("Skills", "")
        summary = candidate.get("Summary", "")
        location = candidate.get("Location", "")

        keywords = f"{skills} {summary}".strip()
        result = query_jobs(keywords=keywords, location=location, max_results=10)

        return jsonify({
            "email": email,
            "location": location,
            "country_detected": detect_country(location),
            "keywords_used": keywords,
            "job_count": result.get("count", 0),
            "examples": result.get("examples", [])
        })
    except Exception as e:
        print(f"🔥 Error in /debug_jobs: {e}")
        return jsonify({"error": str(e)}), 500

# ------------------- MATCH JOBS -------------------

@app.route("/match_jobs", methods=["POST"])
def match_jobs_route():
    try:
        data = request.get_json()
        email = data.get("email")
        if not email:
            return jsonify({"error": "Missing email"}), 400

        client = get_gspread_client()

        # Load candidate info
        cand_sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
        candidates = cand_sheet.get_all_records()
        candidate = next((r for r in candidates if r["Email"] == email), None)
        if not candidate:
            return jsonify({"error": "Candidate not found"}), 404

        candidate_summary = candidate.get("Summary", "")
        candidate_location = candidate.get("Location", "")
        if not candidate_summary.strip():
            return jsonify({"error": "Candidate summary is empty"}), 400

        full_candidate_text = f"{candidate_summary}. Location: {candidate_location}"

        # Load job listings
        job_sheet = client.open_by_key(os.getenv("JOBS_SHEET_ID")).sheet1
        job_rows = [r for r in job_sheet.get_all_records() if r.get("Job Summary")]

        if not job_rows:
            return jsonify({"error": "No job summaries found"}), 404

        for job in job_rows:
            job["embedding_input"] = f"{job.get('Job Summary', '')}. Location: {job.get('Location', '')}"

        top_matches = match_jobs(full_candidate_text, job_rows)

        def extract_keywords(text):
            words = text.lower().split()
            return set(w.strip(".,()") for w in words if len(w) > 3)

        candidate_keywords = extract_keywords(candidate_summary)

        return jsonify({
            "email": email,
            "top_matches": [
                {
                    "summary": match[0].get("Job Summary", ""),
                    "location": match[0].get("Location", ""),
                    "score": round(float(match[1]), 4),
                    "reason": ", ".join(candidate_keywords & extract_keywords(match[0].get("Job Summary", ""))) or "Similar topic and context"
                } for match in top_matches
            ]
        })
    except Exception as e:
        print(f"🔥 Error in /match_jobs: {e}")
        return jsonify({"error": str(e)}), 500

# ------------------- EMPLOYER DASHBOARD -------------------

@app.route("/employer_dashboard", methods=["GET"])
def employer_dashboard():
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
        records = sheet.get_all_records()

        anonymized = []
        for idx, r in enumerate(records):
            anonymized.append({
                "id": idx,
                "summary": r.get("Summary", "No summary provided"),
                "skills": r.get("Skills", "No skills listed"),
                "location": r.get("Location", "Unknown")
            })

        return render_template("employer_dashboard.html", candidates=anonymized)
    except Exception as e:
        print(f"🔥 Error in /employer_dashboard: {e}")
        return "Employer dashboard failed", 500

# ------------------- UNLOCK PROFILE -------------------

@app.route("/unlock/<int:candidate_id>", methods=["GET"])
def unlock_candidate(candidate_id):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
        candidates = sheet.get_all_records()

        if candidate_id < 0 or candidate_id >= len(candidates):
            return "Candidate not found", 404

        candidate = candidates[candidate_id]
        return render_template("unlocked_candidate.html", candidate=candidate)
    except Exception as e:
        print(f"🔥 Error in /unlock/{candidate_id}: {e}")
        return "Unlock failed", 500

# ------------------- HOME -------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "AI Talent Marketplace backend is running"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
