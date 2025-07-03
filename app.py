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
