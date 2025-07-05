import os
import json
import base64
import time
from dotenv import load_dotenv
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Load environment variables
load_dotenv()

# OpenAI settings
openai.api_key = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

# Google Sheets settings
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
if not creds_path:
    raise EnvironmentError("Missing GOOGLE_CREDENTIALS_PATH environment variable.")

creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1

def get_embedding(text, model=EMBEDDING_MODEL):
    response = openai.Embedding.create(model=model, input=text)
    return response.data[0]["embedding"]

def serialize_embedding(embedding):
    return base64.b64encode(json.dumps(embedding).encode()).decode()

def precompute_embeddings():
    records = sheet.get_all_records()
    header = sheet.row_values(1)

    # Ensure 'Embedding' column exists
    if "Embedding" not in header:
        sheet.update_cell(1, len(header) + 1, "Embedding")
        header.append("Embedding")

    embedding_col_index = header.index("Embedding") + 1

    for i, row in enumerate(records, start=2):
        summary = row.get("Summary", "").strip()
        already_embedded = row.get("Embedding", "").strip()

        if not summary:
            print(f"⏭️ Row {i}: No summary found. Skipping.")
            continue
        if already_embedded:
            print(f"✅ Row {i}: Embedding already exists. Skipping.")
            continue

        try:
            print(f"🔄 Row {i}: Computing embedding...")
            embedding = get_embedding(summary)
            encoded = serialize_embedding(embedding)
            sheet.update_cell(i, embedding_col_index, encoded)
            print(f"✅ Row {i}: Embedding stored.")
            time.sleep(1)  # Rate limiting
        except Exception as e:
            print(f"❌ Row {i}: Error occurred: {e}")
            time.sleep(3)  # Backoff for errors

if __name__ == "__main__":
    precompute_embeddings()
