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
            data = request.get_json()  # Get form data from POST request
            name = data.get("name")  # Extract Name (candName)
            email = data.get("email")  # Extract Email (candEmail)
            skills = data.get("skills")  # Extract Skills (candSkills)

            # Validate required fields
            if not email or not name or not skills:
                return jsonify({"success": False, "error": "Email, name, and skills are required."}), 400

            # Hash the password (password is handled in the sign-up process already, so not used here)
            # If you are handling a new password, you could add password hashing like:
            # password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            client = get_gspread_client()  # Get the gspread client

            # ------------------- USERS SHEET -------------------
            users_sheet = client.open_by_key(os.getenv("USERS_SHEET_ID")).sheet1
            users = users_sheet.get_all_records()

            # Check if the email already exists in the Users sheet
            if any(row["Email"] == email for row in users):
                return jsonify({"success": False, "error": "Email already registered."}), 400

            # Append new user to the Users Sheet
            # users_sheet.append_row([email, password_hash])  # Uncomment if storing password
            users_sheet.append_row([email, "", ""])  # Assuming password is stored elsewhere (e.g., password is handled in another part of the system)
            print(f"✅ Registered user: {email} in USERS sheet")

            # ------------------- CANDIDATES SHEET -------------------
            candidates_sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
            candidate_emails = [row["Email"] for row in candidates_sheet.get_all_records()]

            # If the email doesn't exist in the Candidates Sheet, add a new row
            if email not in candidate_emails:
                candidates_sheet.append_row([email, name, skills, ""])  # Email | Name | Skills | Timestamp (blank)
                print(f"✅ Created profile for: {email} in CANDIDATES sheet")
            else:
                print(f"ℹ️ Candidate already exists in CANDIDATES sheet")

            # Respond with success and a dashboard link
            dashboard_link = f"https://ai-talent-marketplace.onrender.com/dashboard"
            return jsonify({
                "success": True,
                "message": "Registration successful.",
                "dashboard_link": dashboard_link
            })

        except Exception as e:
            print(f"🔥 Error in register_user: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
