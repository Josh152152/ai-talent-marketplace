from flask import Flask, request, jsonify, session, redirect, render_template
from flask_cors import CORS
from functools import wraps
import os
import sys
from dotenv import load_dotenv
from sheets import get_gspread_client
from candidate_registration import CandidateRegistrationSystem
from matching_system import MatchingSystem

# Ensure print() flushes immediately to logs
sys.stdout.reconfigure(line_buffering=True)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# 🔐 Set a secret key for sessions
app.secret_key = os.getenv("APP_SECRET_KEY", "super-secret-key")  # Secure in .env

registration = CandidateRegistrationSystem()
matcher = MatchingSystem()

# ------------------- AUTH LOGIC -------------------

# ✅ Hardcoded admin credentials (can move to .env later)
AUTHORIZED_USERS = {
    "admin@example.com": "securepassword"
}

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

# ------------------- EXISTING ROUTES -------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "AI Talent Marketplace backend is running"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

@app.route("/test_sheets", methods=["GET"])
def test_sheets():
    try:
        client = get_gspread_client()
        sheets = {
            "candidates": os.getenv("CANDIDATES_SHEET_ID"),
            "employers": os.getenv("EMPLOYERS_SHEET_ID"),
            "companies": os.getenv("COMPANIES_SHEET_ID"),
            "users": os.getenv("USERS_SHEET_ID")
        }

        results = {}
        for name, sheet_id in sheets.items():
            try:
                print(f"🔍 Trying to access '{name}' sheet with ID: {sheet_id}")
                sheet = client.open_by_key(sheet_id)
                data = sheet.sheet1.get_all_records()
                results[name] = data[0] if data else None
                print(f"✅ Successfully accessed '{name}'")
            except Exception as e:
                print(f"❌ Failed to access '{name}': {e}")
                raise e

        return jsonify({"success": True, "samples": results})
    except Exception as e:
        print(f"🔥 ERROR in /test_sheets: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/register_candidate", methods=["POST"])
def register_candidate():
    return registration.register(request, sheet_type="candidates")

@app.route("/register_job", methods=["POST"])
def register_job():
    return registration.register(request, sheet_type="employers")

@app.route("/find_matches", methods=["POST"])
def find_matches():
    try:
        job = request.json
        client = get_gspread_client()
        candidates = client.open_by_key(os.getenv('CANDIDATES_SHEET_ID')).sheet1.get_all_records()
        matches = matcher.find_matches(job, candidates)
        return jsonify({"success": True, "matches": matches})
    except Exception as e:
        print(f"🔥 ERROR in /find_matches: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ------------------- RUN APP -------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
