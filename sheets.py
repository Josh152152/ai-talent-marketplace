import os
import gspread
from google.oauth2.service_account import Credentials

def get_gspread_client():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds_path = os.getenv('GOOGLE_CREDENTIALS_PATH', '/etc/secrets/credentials.json')
    creds = Credentials.from_service_account_file(creds_path, scopes=scope)
    return gspread.authorize(creds)
