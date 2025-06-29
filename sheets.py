import os
import gspread
from google.oauth2.service_account import Credentials

def get_gspread_client():
    creds = Credentials.from_service_account_file(
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS")  # this should be 'credentials.json'
    )
    return gspread.authorize(creds)
