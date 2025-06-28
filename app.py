from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from candidate_registration import CandidateRegistrationSystem
from matching_system import MatchingSystem

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

def get_gspread_clients():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', '/etc/secrets/credentials.json')
    creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH, scopes=scope)
    client = gspread.authorize(creds)
    return {
        "candidates": client.open_by_key(os.getenv('CANDIDATES_SHEET_ID')),
        "employers": client.open_by_key(os.getenv('EMPLOYERS_SHEET_ID')),
        "companies": client.open_by_key(os.getenv('COMPANIES_SHEET_ID')),
        "users": client.open_by_key(os.getenv('USERS_SHEET_ID'))
    }

registration = CandidateRegistrationSystem()
matcher = MatchingSystem()

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "AI Talent Marketplace backend is running"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

@app.route("/test_sheets", methods=["GET"])
def test_sheets():
    try:
        print("📄 Testing Google Sheet access...")

        client = get_gspread_clients()
        results = {}

        for key in ["candidates", "employers", "companies", "users"]:
            try:
                sheet = client[key]
                data = sheet.sheet1.get_all_records()
                print(f"✅ Accessed '{key}' sheet: {len(data)} rows found")
                results[key] = data[0] if data else None
            except Exception as e:
                print(f"❌ Error accessing '{key}' sheet: {e}")
                raise e

        return jsonify({
            "success": True,
            "samples": {
                "candidate": results.get("candidates"),
                "job": results.get("employers"),
                "company": results.get("companies"),
                "user": results.get("users")
            }
        })

    except Exception as e:
        print(f"🔥 ERROR in /test_sheets: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/register_user", methods=["POST"])
def register_user():
    return registration.register(request)

@app.route("/find_matches", methods=["POST"])
def find_matches():
    try:
        job = request.json
        sheets = get_gspread_clients()
        candidates = sheets["candidates"].sheet1.get_all_records()
        matches = matcher.find_matches(job, candidates)
        return jsonify({"success": True, "matches": matches})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
