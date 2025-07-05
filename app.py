from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
import os
import sys
from dotenv import load_dotenv

# Load environment variables
sys.stdout.reconfigure(line_buffering=True)
load_dotenv()

# Core setup
app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("APP_SECRET_KEY", "super-secret-key")

# Import project modules
from sheets import get_gspread_client
from candidate_registration import CandidateRegistrationSystem
from matching_system import MatchingSystem
from adzuna_helper import query_jobs, detect_country
from smart_matcher import match_jobs
from auth import auth  # 🔐 Auth Blueprint

# Register blueprints
app.register_blueprint(auth)

# Init logic modules
registration = CandidateRegistrationSystem()
matcher = MatchingSystem()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200

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

        return render_template("candidate_dashboard.html", data={"Email": email, "Name": "Candidate", "Summary": "Not set yet"})
    except Exception as e:
        print(f"🔥 Error in /dashboard: {e}")
        return "Dashboard error", 500

@app.route("/update_summary", methods=["POST"])
def update_summary():
    try:
        email = request.form.get("email")
        new_summary = request.form.get("summary", "")
        if not email:
            return "Missing email", 400

        client = get_gspread_client()
        sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
        records = sheet.get_all_records()

        for i, row in enumerate(records):
            if row.get("Email") == email:
                # Column 5 = Summary
                sheet.update_cell(i + 2, 5, new_summary)
                return redirect(f"/dashboard?email={email}")

        return "Candidate not found.", 404
    except Exception as e:
        print(f"🔥 Error in /update_summary: {e}")
        return "Internal server error", 500

@app.route("/suggest_skills", methods=["POST"])
def suggest_skills():
    try:
        data = request.get_json() or request.form
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

        keyword
