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
from adzuna_helper import query_jobs
from smart_matcher import match_jobs, suggest_missing_skills  # ✅ NEW

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

# ------------------- CANDIDATE PROFILE -------------------

serializer = URLSafeSerializer(os.getenv("APP_SECRET_KEY", "default-secret"))

@app.route("/profile/<token>")
def view_candidate_profile(token):
    try:
        email = serializer.loads(token)

        client = get_gspread_client()
        sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
        records = sheet.get_all_records()

        for row in records:
            if row.get("Email") == email:
                return render_template("candidate_profile.html", data=row)

        return "Profile not found", 404
    except Exception as e:
        print(f"❌ Error in /profile/<token>: {e}")
        return "Invalid or expired profile link", 400

# ------------------- ✅ ADZUNA AI MATCHING -------------------

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

        adzuna_result = query_jobs(keywords=skills, location=location)
        job_titles = adzuna_result.get("examples", [])

        if not job_titles:
            return jsonify({
                "matches_found": 0,
                "location": location,
                "top_matches": [],
                "missing_skills": [],
                "message": "No matching jobs found."
            })

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

# ------------------- SYSTEM ROUTES -------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "AI Talent Marketplace backend is running"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})
