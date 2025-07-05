from flask import Flask
from flask_cors import CORS
import os

from auth import auth
from candidate_registration import CandidateRegistrationSystem
from matching_system import MatchingSystem
from sheets import get_gspread_client  # Ensure you have a get_gspread_client() function in sheets.py

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("APP_SECRET_KEY", "super-secret-key")

# Register Blueprints and services
app.register_blueprint(auth, url_prefix="/auth")  # Changed URL prefix to '/auth'

# Instantiate systems (if used later in other routes)
registration = CandidateRegistrationSystem()
matcher = MatchingSystem()

# Debug route to inspect environment variables (for testing only)
@app.route("/debug/env", methods=["GET"])
def debug_env():
    return {
        "APP_SECRET_KEY": os.getenv("APP_SECRET_KEY"),
        "CANDIDATES_SHEET_ID": os.getenv("CANDIDATES_SHEET_ID"),
        "GOOGLE_CREDENTIALS_PATH": os.getenv("GOOGLE_CREDENTIALS_PATH"),
        "PORT": os.getenv("PORT"),
    }, 200

# Test route to check if the credentials file is accessible
@app.route("/test-credentials")
def test_credentials():
    try:
        with open('/etc/secrets/credentials.json', 'r') as file:
            return "Credentials file is accessible", 200
    except Exception as e:
        return f"Error: {e}", 500

# Test route for Google Sheets integration
@app.route("/test-sheet")
def test_sheet():
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
        records = sheet.get_all_records()
        return {"records": records}, 200
    except Exception as e:
        return f"Error accessing Google Sheets: {e}", 500

# Sanity test route to check signup route registration
@app.route("/signup-test")
def signup_test():
    return "Signup route is alive", 200

# Simple route to confirm server is working correctly
@app.route("/test-server")
def test_server():
    return "Server is live!", 200

# Health check route for Render
@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200

# Print the list of all registered routes (for debugging purposes)
print("🔍 Registered routes:", app.url_map)

# Run the Flask app only in local development (when not using gunicorn)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
