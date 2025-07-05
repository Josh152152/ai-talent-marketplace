from flask import Flask
from flask_cors import CORS
import os

from auth import auth
from candidate_registration import CandidateRegistrationSystem
from matching_system import MatchingSystem

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("APP_SECRET_KEY", "super-secret-key")

# Register Blueprints and services
app.register_blueprint(auth)

# Instantiate systems (if used later in other routes)
registration = CandidateRegistrationSystem()
matcher = MatchingSystem()

# Health check route for Render
@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200

# Optional: Add more routes (e.g., dashboard or APIs) if needed

# Run only in local dev
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
