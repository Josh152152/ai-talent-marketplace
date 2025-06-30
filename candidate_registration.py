import os
import bcrypt
from flask import jsonify
from sheets import get_gspread_client
from itsdangerous import URLSafeSerializer
from datetime import datetime

class CandidateRegistrationSystem:
    def __init__(self):
        self.serializer = URLSafeSerializer(os.getenv("APP_SECRET_KEY", "default-secret"))

    def register(self, request):
        try:
            data = request.get_json()
            name = data.get("name")
            email = data.get("email")
            skills = data.get("skills")
            location = data.get("location")
            summary = data.get("summary")

            # Validate required fields
            if not email or not name or not skills or not location or not summary:
                return jsonify({
                    "success": False,
                    "error": "Email, name, skills, location, and summary are required."
                }), 400

            client = get_gspread_client()

            # ------------------- USERS SHEET -------------------
            users_sheet = client.open_by_key(os.getenv("USERS_SHEET_ID")).sheet1
            users = users_sheet.get_all_records()

            # Check if the email already exists in the Users sheet
            if any(row["Email"] == email for row in users):
                return jsonify({"success": False, "error": "Email already registered."}), 400

            # Append new user to the Users Sheet
            users_sheet.append_row([email, "", ""])  # Password handled elsewhere
            print(f"✅ Registered user: {email} in USERS sheet")

            # ------------------- CANDIDATES SHEET -------------------
            candidates_sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
            candidate_emails = [row["Email"] for row in candidates_sheet.get_all_records()]

            if email not in candidate_emails:
                timestamp = datetime.now().isoformat()
                candidates_sheet.append_row([email, name, skills, location, summary, timestamp])
                print(f"✅ Created profile for: {email} in CANDIDATES sheet")
            else:
                print(f"ℹ️ Candidate already exists in CANDIDATES sheet")

            dashboard_link = f"https://ai-talent-marketplace.onrender.com/dashboard"
            return jsonify({
                "success": True,
                "message": "Registration successful.",
                "dashboard_link": dashboard_link
            })

        except Exception as e:
            print(f"🔥 Error in register_user: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
