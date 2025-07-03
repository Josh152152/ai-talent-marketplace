# (All your previous imports here)
from adzuna_helper import query_jobs, detect_country  # Make sure detect_country is included

# ... rest of your existing code above remains unchanged ...

# ------------------- 🔍 AI SKILL EXPANSION -------------------

@app.route("/suggest_skills", methods=["POST"])
def suggest_skills():
    try:
        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"error": "Email is required"}), 400

        client = get_gspread_client()
        sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
        records = sheet.get_all_records()

        candidate = next((r for r in records if r["Email"] == email), None)
        if not candidate:
            return jsonify({"error": "Candidate not found"}), 404

        skills = [s.strip().lower() for s in candidate.get("Skills", "").split(",") if s.strip()]
        location = candidate.get("Location", "")

        from adzuna_helper import suggest_skill_expansion
        suggestions = suggest_skill_expansion(skills, location)

        return jsonify({
            "email": email,
            "suggested_skills": suggestions
        })

    except Exception as e:
        print(f"🔥 Error in /suggest_skills: {e}")
        return jsonify({"error": str(e)}), 500

# ------------------- 🛠 DEBUG: TEST ADZUNA RAW JOBS -------------------

@app.route("/debug_jobs", methods=["POST"])
def debug_jobs():
    try:
        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"error": "Missing email"}), 400

        client = get_gspread_client()
        sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
        records = sheet.get_all_records()

        candidate = next((r for r in records if r["Email"] == email), None)
        if not candidate:
            return jsonify({"error": "Candidate not found"}), 404

        skills = candidate.get("Skills", "")
        summary = candidate.get("Summary", "")
        location = candidate.get("Location", "")

        keywords = f"{skills} {summary}".strip()
        result = query_jobs(keywords=keywords, location=location, max_results=10)

        return jsonify({
            "email": email,
            "location": location,
            "country_detected": detect_country(location),
            "keywords_used": keywords,
            "job_count": result.get("count", 0),
            "examples": result.get("examples", [])
        })

    except Exception as e:
        print(f"🔥 Error in /debug_jobs: {e}")
        return jsonify({"error": str(e)}), 500

# ------------------- SYSTEM ROUTES -------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "AI Talent Marketplace backend is running"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
