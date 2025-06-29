import os
import gspread
from google.oauth2.service_account import Credentials

def get_gspread_client():
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH")  # uses correct key
    print(f"📁 Loading credentials from: {creds_path}")  # optional debug
    creds = Credentials.from_service_account_file(creds_path)
    return gspread.authorize(creds)
