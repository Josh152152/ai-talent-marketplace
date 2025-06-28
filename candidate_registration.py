import os
from flask import jsonify
from app import get_gspread_client  # Adjust if app.py is in another folder

class CandidateRegistrationSystem:
    def __init__(self):
        pass  # No external resource access here

    def register(self, request):
        try:
            data = request.get_json()
            name = data.get("name")
            email = data.get("email")
            skills = data.get("skills")
            timestamp = data.get("timestamp")

            # Access the sheet *inside* the method
            client = get_gspread_client()
            sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
            sheet.append_row([name, email, skills, timestamp])

            return jsonify({"success": True, "message": "Candidate registered."})
        except Exception as e:
            print(f"🔥 Error in register_user: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
