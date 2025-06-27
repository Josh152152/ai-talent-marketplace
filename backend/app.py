from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from matching_system import MatchingSystem
from candidate_registration import CandidateRegistrationSystem

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Google Sheets setup
scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive']

creds = Credentials.from_service_account_file(
    os.getenv('GOOGLE_CREDENTIALS_PATH'),
    scopes=scope
)

client = gspread.authorize(creds)

# Open the sheets
candidates_sheet = client.open_by_key(os.getenv('CANDIDATES_SHEET_ID'))
employers_sheet = client.open_by_key(os.getenv('EMPLOYERS_SHEET_ID'))
companies_sheet = client.open_by_key(os.getenv('COMPANIES_SHEET_ID'))

# Initialize systems
matching_system = MatchingSystem()
registration_system = CandidateRegistrationSystem(
    credentials_path=os.getenv('GOOGLE_CREDENTIALS_PATH'),
    users_sheet_id=os.getenv('USERS_SHEET_ID', '')
)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "AI Talent Marketplace backend is running"})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

@app.route('/test_sheets', methods=['GET'])
def test_sheets():
    try:
        candidates_data = candidates_sheet.sheet1.get_all_records()
        employers_data = employers_sheet.sheet1.get_all_records()
        companies_data = companies_sheet.sheet1.get_all_records()
        return jsonify({
            "success": True,
            "samples": {
                "candidate": candidates_data[0] if candidates_data else None,
                "job": employers_data[0] if employers_data else None,
                "company": companies_data[0] if companies_data else None,
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/get_jobs', methods=['GET'])
def get_jobs():
    try:
        jobs_data = employers_sheet.sheet1.get_all_records()
        return jsonify({"success": True, "jobs": jobs_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/get_candidates', methods=['GET'])
def get_candidates():
    try:
        candidates_data = candidates_sheet.sheet1.get_all_records()
        return jsonify({"success": True, "candidates": candidates_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/find_matches', methods=['POST'])
def find_matches():
    try:
        job_data = request.json
        candidates_data = candidates_sheet.sheet1.get_all_records()
        candidates_df = pd.DataFrame(candidates_data)
        matches = matching_system.find_matches(job_data, candidates_df)
        return jsonify({"success": True, "matches": matches})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/add_candidate', methods=['POST'])
def add_candidate():
    try:
        candidate_data = request.json
        candidate_id = f"CAN_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        row = [candidate_id] + [candidate_data.get(field, '') for field in [
            'full_name', 'email', 'phone', 'location', 'current_position',
            'years_experience', 'skills', 'education', 'languages',
            'portfolio_url', 'linkedin_url', 'github_url', 'expected_salary',
            'notice_period', 'work_authorization', 'willing_to_relocate',
            'preferred_locations', 'achievements', 'profile_summary'
        ]] + [datetime.now().isoformat(), 'active']
        candidates_sheet.sheet1.append_row(row)
        return jsonify({"success": True, "candidate_id": candidate_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/add_job', methods=['POST'])
def add_job():
    try:
        job_data = request.json
        job_id = f"JOB_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        row = [job_id] + [job_data.get(field, '') for field in [
            'company_name', 'job_title', 'department', 'location',
            'employment_type', 'experience_required', 'salary_range',
            'job_description', 'required_skills', 'preferred_skills',
            'education_requirement', 'benefits', 'application_deadline',
            'contact_email', 'contact_phone', 'company_website',
            'remote_work_option', 'visa_sponsorship']
        ] + [datetime.now().isoformat(), 'active']
        employers_sheet.sheet1.append_row(row)
        return jsonify({"success": True, "job_id": job_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
