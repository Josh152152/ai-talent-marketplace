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

# 📦 Register Blueprints and services
print("📦 Registering auth blueprint...")
app.register_blueprint(auth)

# 🔧 Instantiate systems
registration = CandidateRegistrationSystem()
matcher = MatchingSystem()

# ✅ Health check route
@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200

# ✅ Test route to confirm app is live
@app.route("/test", methods=["GET"])
def test():
    return "✅ Flask main route is working!", 200

# 📋 Print registered routes at startup
@app.before_first_request
def show_routes():
    print("\n🚀 Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"🛣️  {rule}")
    print()

# Run only in local dev (Render uses Gunicorn)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
