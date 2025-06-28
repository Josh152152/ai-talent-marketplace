import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from flask import jsonify
from cryptography.fernet import Fernet

class CandidateRegistrationSystem:
    def __init__(self):
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        self.secret = os.getenv("ENCRYPTION_SECRET").encode()
        self.fernet = Fernet(self.secret)

        creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "/etc/secrets/credentials.json")
        creds = Credentials.from_service_account_file(creds_path, scopes=self.scope)
        client = gspread.authorize(creds)
        self.users_sheet = client.open_by_key(os.getenv("USERS_SHEET_ID")).sheet1

    def register(self, request):
        data = request.json
        try:
            encrypted_pw = self.fernet.encrypt(data["password"].encode()).decode()
            row = [
                data.get("email", ""), 
                encrypted_pw,
                datetime.now().isoformat()
            ]
            self.users_sheet.append_row(row)
            return jsonify({"success": True, "message": "User registered"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
