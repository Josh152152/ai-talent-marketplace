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
from adzuna_helper import query_jobs, detect_country
from smart_matcher import match_jobs, suggest_missing_skills

# Ensure print() flushes immediately to logs
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("APP_SECRET_KEY", "super-secret-key")

registration = CandidateRegistrationSystem()
matcher = MatchingSystem()

# ------------------- AUTH -------------------

AUTHORIZED_USERS = {"admin@example.com": "securepassword"}

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if AUTHORIZED_USERS.get(email) == password:
            session["user"] = email
            return redirect("/admin")
        return "Unauthorized", 401
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/admin")
@login_required
def admin_dashboard():
    return "Welcome to the Admin Dashboard"

# ------------------- CANDIDATE LOGIN -------------------

@app.route("/login_user", methods=["POST"])
def login_user():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"success": False, "error": "Email and password are required."}), 400

        client = get_gspread_client()
        sheet = client.open_by_key(os.getenv("USERS_SHEET_ID")).sheet1
        users = sheet.get_all_records()

        for user in users:
            if user["Email"] == email:
                stored_hash = user["Password_Hash"]
                if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
                    session["user"] = email
                    print(f"🔓 Login successful: {email}")
                    return jsonify({"success": True, "message": "Login successful."})
                else:
                    return jsonify({"success": False, "error": "Incorrect password."}), 401
        return jsonify({"success": False, "error": "User not found."}), 404

    except Exception as e:
        print(f"🔥 Error in /login_user: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/candidate_login", methods=["GET", "POST"])
def candidate_login_form():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        client = get_gspread_client()
        sheet = client.open_by_key(os.getenv("USERS_SHEET_ID")).sheet1
        users = sheet.get_all_records()

        for user in users:
            if user["Email"] == email:
                stored_hash = user["Password_Hash"]
                if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
                    session["user"] = email
                    return redirect("/dashboard")
                else:
                    return "Incorrect password", 401

        return "User not found", 404

    return render_template("candidate_login.html")

# ------------------- CANDIDATE DASHBOARD -------------------

@app.route("/dashboard")
@login_required
def candidate_dashboard():
    try:
        email = session["user"]
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
@login_required
def update_skills():
    try:
        email = session["user"]
        new_skills = request.form.get("skills", "")

        client = get_gspread_client()
        sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
        records = sheet.get_all_records()

        for i, row in enumerate(records):
            if row.get("Email") == email:
                sheet.update_cell(i + 2, 3, new_skills)  # Column 3 = Skills
                return redirect("/dashboard")

        return "Candidate not found.", 404

    except Exception as e:
        print(f"🔥 Error in /update_skills: {e}")
        return "Internal server error", 500

# ------------------- AI SKILL EXPANSION -------------------

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

        return jsonify({
            "email": email,
            "suggested_skills": suggestions
        })

    except Exception as e:
        print(f"🔥 Error in /suggest_skills: {e}")
        return jsonify({"error": str(e)}), 500

# ------------------- DEBUG JOB SEARCH -------------------

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

# ------------------- SYSTEM ROUTES -------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "AI Talent Marketplace backend is running"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

# ------------------- UNLOCK CANDIDATE PROFILE (NEW) -------------------

@app.route("/unlock/<int:candidate_id>", methods=["GET"])
def unlock_candidate(candidate_id):
    """
    Simulates unlocking a candidate's contact info for an employer.
    """
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

# ------------------- MAIN -------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
