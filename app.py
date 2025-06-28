from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
from sentence_transformers import SentenceTransformer, util

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load model once
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_gspread_clients():
    """ Lazily initialize Google Sheets clients when needed. """
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', '/etc/secrets/credentials.json')
    creds = Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_PATH,
        scopes=scope
    )
    client = gspread.authorize(creds)
    return {
        "candidates": client.open_by_key(os.getenv('CANDIDATES_SHEET_ID')),
        "employers": client.open_by_key(os.getenv('EMPLOYERS_SHEET_ID')),
        "companies": client.open_by_key(os.getenv('COMPANIES_SHEET_ID'))
    }

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "AI Talent Marketplace backend is running"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

@app.route("/test_sheets", methods=["GET"])
def test_sheets():
    try:
        sheets = get_gspread_clients()
        candidates_data = sheets["candidates"].sheet1.get_all_records()
        employers_data = sheets["employers"].sheet1.get_all_records()
        companies_data = sheets["companies"].sheet1.get_all_records()
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

@app.route("/find_matches", methods=["POST"])
def find_matches():
    try:
        job_data = request.json
        job_text = job_data.get("job_requirements", "")
        if not job_text:
            return jsonify({"success": False, "error": "Missing 'job_requirements' in request"}), 400

        sheets = get_gspread_clients()
        candidates_data = sheets["candidates"].sheet1.get_all_records()
        candidates_df = pd.DataFrame(candidates_data)

        # Remove rows with empty profile
        candidates_df = candidates_df.dropna(subset=["profile_details"])

        job_embedding = model.encode(job_text, convert_to_tensor=True)

        candidates_df["embedding"] = candidates_df["profile_details"].apply(
            lambda text: model.encode(text, convert_to_tensor=True)
        )

        candidates_df["similarity"] = candidates_df["embedding"].apply(
            lambda emb: util.cos_sim(emb, job_embedding).item()
        )

        top_matches = candidates_df.sort_values(by="similarity", ascending=False).head(3)
        matches = top_matches.drop(columns=["embedding"]).to_dict(orient="records")

        return jsonify({"success": True, "matches": matches})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
