import os
import json
import base64
import time
from dotenv import load_dotenv
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Load .env
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(os.getenv("GOOGLE_CREDENTIALS_PATH"), scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1

def get_embedding(text, model=EMBEDDING_MODEL):
    response = openai.Embedding.create(
        model=model,
        input=text
    )
    return response.data[0]['embedding']

def serialize_embedding(embedding):
    return base64.b64encode(json.dumps(embedding).encode()).decode()

def precompute():
    records = sheet.get_all_records()
    header = sheet.row_values(1)

    if "Embedding" not in header:
        sheet.update_cell(1, len(header) + 1, "Embedding")
        header.append("Embedding")

    embedding_col_index = header.index("Embedding") + 1

    for i, row in enumerate(records, start=2):  # Start from row 2 (after header)
        summary = row.get("Summary", "").strip()
        existing = row.get("Embedding", "").strip()

        if not summary:
            print(f"⏭️ Row {i}: No summary.")
            continue
        if existing:
            print(f"✅ Row {i}: Already has embedding.")
            continue

        try:
            print(f"🔄 Processing row {i}...")
            embedding = get_embedding(summary)
            encoded = serialize_embedding(embedding)
            sheet.update_cell(i, embedding_col_index, encoded)
            print(f"✅ Row {i}: Embedding stored.")
            time.sleep(1)  # Avoid hitting rate limit

        except Exception as e:
            print(f"❌ Error on row {i}: {e}")
            time.sleep(3)  # Wait before retrying

if __name__ == "__main__":
    precompute()
