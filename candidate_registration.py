import os
from flask import jsonify
from sheets import get_gspread_client  # ✅ No more circular import

class CandidateRegistrationSystem:
    def __init__(self):
        pass

    def register(self, request):
        try:
            data = request.get_json()
            name = data.get("name")
            email = data.get("email")
            skills = data.get("skills")
            timestamp = data.get("timestamp")

            client = get_gspread_client()
            sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
            sheet.append_row([name, email, skills, timestamp])

            return jsonify({"success": True, "message": "Candidate registered."})
        except Exception as e:
            print(f"🔥 Error in register_user: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
