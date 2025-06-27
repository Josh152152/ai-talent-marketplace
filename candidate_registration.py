import gspread
from google.oauth2.service_account import Credentials
from cryptography.fernet import Fernet
import os
import hashlib
import base64
from dotenv import load_dotenv

load_dotenv()

class CandidateRegistrationSystem:
    def __init__(self, credentials_path, users_sheet_id):
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = Credentials.from_service_account_file(credentials_path, scopes=self.scope)
        self.client = gspread.authorize(self.creds)
        self.users_sheet = self.client.open_by_key(users_sheet_id)
        self.key = self._get_encryption_key()
        self.fernet = Fernet(self.key)

    def _get_encryption_key(self):
        secret = os.getenv("ENCRYPTION_SECRET", "default_secret")
        hash = hashlib.sha256(secret.encode()).digest()
        return base64.urlsafe_b64encode(hash)

    def register_candidate(self, username, email, password):
        sheet = self.users_sheet.sheet1
        existing_users = sheet.get_all_records()

        for user in existing_users:
            if user['username'] == username or user['email'] == email:
                return {"success": False, "error": "Username or email already exists."}

        encrypted_password = self.fernet.encrypt(password.encode()).decode()
        user_id = f"USR_{len(existing_users) + 1:04d}"

        new_row = [user_id, username, email, encrypted_password, '', '', '', '', '']
        sheet.append_row(new_row)

        return {"success": True, "user_id": user_id, "message": "User registered successfully.", "sheet_id": self.users_sheet.id}

    def login_candidate(self, username, password):
        sheet = self.users_sheet.sheet1
        users = sheet.get_all_records()

        for user in users:
            if user['username'] == username:
                try:
                    decrypted_password = self.fernet.decrypt(user['password'].encode()).decode()
                    if decrypted_password == password:
                        return {"success": True, "user": user}
                    else:
                        return {"success": False, "error": "Invalid password."}
                except Exception:
                    return {"success": False, "error": "Password decryption failed."}

        return {"success": False, "error": "User not found."}

    def get_user_by_id(self, user_id):
        sheet = self.users_sheet.sheet1
        users = sheet.get_all_records()

        for user in users:
            if user['user_id'] == user_id:
                return {"success": True, "user": user}

        return {"success": False, "error": "User not found."}
