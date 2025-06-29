import os
import bcrypt
from flask import jsonify
from sheets import get_gspread_client
from itsdangerous import URLSafeSerializer  # already used

class CandidateRegistrationSystem:
    def __init__(self):
        self.serializer = URLSafeSerializer(os.getenv("APP_SECRET_KEY", "default-secret"))

    def register(self, request):
        try:
            data = request.get_json()
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                return jsonify({"success": False, "error": "Email and password are required."}), 400

            # ✅ Hash the password securely
            password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            client = get_gspread_client()

            # ------------------- USERS SHEET -------------------
            users_sheet = client.open_by_key(os.getenv("USERS_SHEET_ID")).sheet1
            users = users_sheet.get_all_records()

            if any(row["Email"] == email for row in users):
                return jsonify({"success": False, "error": "Email already registered."}), 400

            users_sheet.append_row([email, password_hash])
            print(f"✅ Registered user: {email} in USERS sheet")

            # ------------------- CANDIDATES SHEET -------------------
            candidates_sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
            candidate_emails = [row["Email"] for row in candidates_sheet.get_all_records()]
            if email not in candidate_emails:
                candidates_sheet.append_row([email, "", ""])  # Email | Skills | Timestamp (blank)
                print(f"✅ Created blank profile for: {email} in CANDIDATES sheet")

            # ------------------- Secure Dashboard Link -------------------
            token = self.serializer.dumps(email)
            dashboard_link = f"https://ai-talent-marketplace.onrender.com/dashboard"

            return jsonify({
                "success": True,
                "message": "Registration successful.",
                "dashboard_link": dashboard_link
            })

        except Exception as e:
            print(f"🔥 Error in register_user: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
