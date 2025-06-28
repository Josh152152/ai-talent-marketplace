import os
from flask import jsonify
from sheets import get_gspread_client  # ✅ No more circular import

class CandidateRegistrationSystem:
    def __init__(self):
        pass

    def register(self, request, sheet_type="candidates"):
        try:
            data = request.get_json()
            name = data.get("name")
            email = data.get("email")
            skills = data.get("skills")
            timestamp = data.get("timestamp")

            client = get_gspread_client()

            # Determine which sheet to write to
            sheet_id_key = {
                "candidates": "CANDIDATES_SHEET_ID",
                "employers": "EMPLOYERS_SHEET_ID"
            }.get(sheet_type)

            if not sheet_id_key:
                raise ValueError(f"Invalid sheet type: {sheet_type}")

            sheet_id = os.getenv(sheet_id_key)
            sheet = client.open_by_key(sheet_id).sheet1
            sheet.append_row([name, email, skills, timestamp])

            return jsonify({"success": True, "message": f"{sheet_type.capitalize()} registered."})
        except Exception as e:
            print(f"🔥 Error in register_user ({sheet_type}): {e}")
            return jsonify({"success": False, "error": str(e)}), 500
