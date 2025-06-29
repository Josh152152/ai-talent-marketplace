import os
import gspread
from google.oauth2.service_account import Credentials

def get_gspread_client():
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH")  # should point to credentials.json
    print(f"📁 Loading credentials from: {creds_path}")  # helpful for debugging

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    return gspread.authorize(creds)
