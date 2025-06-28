class MatchingSystem:
    def __init__(self):
        pass

def find_matches():
    try:
        job = request.json
        print(f"🔍 Incoming job data: {job}")

        client = get_gspread_client()
        sheet = client.open_by_key(os.getenv('CANDIDATES_SHEET_ID')).sheet1
        candidates = sheet.get_all_records()
        print(f"📋 Loaded {len(candidates)} candidates")

        matches = matcher.find_matches(job, candidates)
        print(f"✅ Found {len(matches)} matches")

        return jsonify({"success": True, "matches": matches})
    except Exception as e:
        print(f"🔥 ERROR in /find_matches: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
