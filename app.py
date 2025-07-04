# ... [ALL YOUR EXISTING IMPORTS AND ROUTES ABOVE REMAIN UNCHANGED] ...

# ------------------- SYSTEM ROUTES -------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "AI Talent Marketplace backend is running"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

# ------------------- UNLOCK CANDIDATE ROUTE (NEW) -------------------

@app.route("/unlock/<int:candidate_id>", methods=["GET"])
def unlock_candidate(candidate_id):
    """
    Allows employers to view full candidate info by index (for now, no payment required).
    """
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
        candidates = sheet.get_all_records()

        if candidate_id < 0 or candidate_id >= len(candidates):
            return "Candidate not found", 404

        candidate = candidates[candidate_id]

        return render_template("unlocked_candidate.html", candidate=candidate)

    except Exception as e:
        print(f"🔥 Error in /unlock/{candidate_id}: {e}")
        return "Unlock failed", 500

# ------------------- MAIN -------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
