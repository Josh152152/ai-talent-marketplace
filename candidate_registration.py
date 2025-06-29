import os
from flask import jsonify
from sheets import get_gspread_client
from itsdangerous import URLSafeSerializer  # ✅ NEW

class CandidateRegistrationSystem:
    def __init__(self):
        # ✅ Serializer setup (once)
        self.serializer = URLSafeSerializer(os.getenv("APP_SECRET_KEY", "default-secret"))

    def register(self, request, sheet_type="candidates"):
        try:
            data = request.get_json()
            name = data.get("name")
            email = data.get("email")
            skills = data.get("skills")
            timestamp = data.get("timestamp")

            print(f"📥 Received registration for '{sheet_type}':")
            print(f"    - Name: {name}")
            print(f"    - Email: {email}")
            print(f"    - Skills: {skills}")
            print(f"    - Timestamp: {timestamp}")

            client = get_gspread_client()

            # Get the corresponding sheet ID
            sheet_id_key = {
                "candidates": "CANDIDATES_SHEET_ID",
                "employers": "EMPLOYERS_SHEET_ID"
            }.get(sheet_type)

            if not sheet_id_key:
                raise ValueError(f"Invalid sheet type: {sheet_type}")

            sheet_id = os.getenv(sheet_id_key)
            print(f"📄 Using Google Sheet ID: {sheet_id}")

            # Append to Google Sheet
            sheet = client.open_by_key(sheet_id).sheet1
            sheet.append_row([name, email, skills, timestamp])
            print(f"✅ Appended row to '{sheet_type}' sheet successfully.")

            # ✅ Generate secure profile link if candidate
            if sheet_type == "candidates":
                token = self.serializer.dumps(email)
                profile_url = f"https://your-app-name.onrender.com/profile/{token}"
                print(f"🔗 Candidate profile link: {profile_url}")
                return jsonify({
                    "success": True,
                    "message": "Candidate registered.",
                    "profile_link": profile_url
                })

            return jsonify({
                "success": True,
                "message": f"{sheet_type.capitalize()} registered."
            })

        except Exception as e:
            print(f"🔥 Error in register_user ({sheet_type}): {e}")
            return jsonify({"success": False, "error": str(e)}), 500
