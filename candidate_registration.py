import os
import bcrypt
from flask import jsonify
from sheets import get_gspread_client
from itsdangerous import URLSafeSerializer

class CandidateRegistrationSystem:
    def __init__(self):
        self.serializer = URLSafeSerializer(os.getenv("APP_SECRET_KEY", "default-secret"))

    def register(self, request, sheet_type="candidates"):
        try:
            data = request.get_json()
            name = data.get("name")
            email = data.get("email")
            password = data.get("password")
            skills = data.get("skills", "")
            timestamp = data.get("timestamp")

            if not email or not password:
                return jsonify({"success": False, "error": "Email and password are required."}), 400

            client = get_gspread_client()

            # ✅ Check if email already exists in USERS sheet
            users_sheet = client.open_by_key(os.getenv("USERS_SHEET_ID")).sheet1
            existing_emails = [row["Email"] for row in users_sheet.get_all_records()]
            if email in existing_emails:
                return jsonify({"success": False, "error": "Email already registered."}), 400

            # ✅ Hash password and save to USERS sheet
            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            users_sheet.append_row([email, hashed])
            print(f"✅ User added to USERS sheet: {email}")

            # ✅ Save candidate details to CANDIDATES sheet
            candidates_sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
            candidates_sheet.append_row([name, email, skills, timestamp])
            print(f"📄 Candidate info saved for: {name}")

            # ✅ Create secure dashboard link
            token = self.serializer.dumps(email)
            dashboard_link = f"https://ai-talent-marketplace.onrender.com/dashboard"

            return jsonify({
                "success": True,
                "message": "Registration complete.",
                "dashboard_link": dashboard_link
            })

        except Exception as e:
            print(f"🔥 Error in candidate registration: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
