import os
from your_flask_app_file import get_gspread_client  # Adjust import path as needed

class CandidateRegistrationSystem:
    def __init__(self):
        pass  # No sheet access here

    def register(self, request):
        data = request.get_json()
        candidate = {
            "name": data.get("name"),
            "email": data.get("email"),
            "skills": data.get("skills"),
            "timestamp": data.get("timestamp")
        }

        try:
            client = get_gspread_client()
            sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
            sheet.append_row([candidate["name"], candidate["email"], candidate["skills"], candidate["timestamp"]])
            return {"success": True, "message": "Candidate registered."}
        except Exception as e:
            print(f"🔥 ERROR in candidate registration: {e}")
            return {"success": False, "error": str(e)}
