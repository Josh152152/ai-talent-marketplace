import os
import bcrypt
from flask import jsonify
from sheets import get_gspread_client
from itsdangerous import URLSafeSerializer
from datetime import datetime, timedelta
import requests
from openai import OpenAI
from adzuna_helper import detect_country  # Make sure this exists and is imported

class CandidateRegistrationSystem:
    def __init__(self):
        self.serializer = URLSafeSerializer(os.getenv("APP_SECRET_KEY", "default-secret"))
        self.openai_client = OpenAI()
        self.adzuna_app_id = os.getenv("ADZUNA_APP_ID")
        self.adzuna_app_key = os.getenv("ADZUNA_APP_KEY")

    def extract_job_title(self, skills_summary):
        prompt = f"Based on these skills and summary, suggest the most relevant job title:\n{skills_summary}\nJob Title:"
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.0,
        )
        job_title = response.choices[0].message.content.strip()
        return job_title

    def query_adzuna_job_counts(self, job_title, location, radius_km=50):
        if not self.adzuna_app_id or not self.adzuna_app_key:
            print("⚠️ Missing Adzuna credentials")
            return 0

        country_code = detect_country(location)
        base_url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1"

        params = {
            "app_id": self.adzuna_app_id,
            "app_key": self.adzuna_app_key,
            "what": job_title,
            "where": location,
            "results_per_page": 1,
            "distance": radius_km,
            "date_posted": "last-30-days",  # supported param for last 30 days
        }

        try:
            print(f"Querying Adzuna API with URL: {base_url}")
            print(f"Parameters: {params}")
            res = requests.get(base_url, params=params)
            if res.status_code == 200:
                data = res.json()
                total_count = data.get("count", 0)
                print(f"Jobs found: {total_count}")
                return total_count
            else:
                print(f"⚠️ Adzuna API error: {res.status_code} - {res.text}")
                return 0
        except Exception as e:
            print(f"🔥 Exception querying Adzuna: {e}")
            return 0

    def get_job_counts_over_time(self, job_title, location, radius_km=50, months=6):
        """
        Returns a list of dicts with monthly job counts over the past `months` months.
        Each dict contains: {"month": "YYYY-MM", "count": int}

        NOTE: If Adzuna API rejects date_posted_min/max parameters,
        this function might need to be adjusted or simplified.
        """
        if not self.adzuna_app_id or not self.adzuna_app_key:
            print("⚠️ Missing Adzuna credentials")
            return []

        country_code = detect_country(location)
        base_url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1"
        today = datetime.utcnow().date()

        monthly_counts = []

        for i in range(months - 1, -1, -1):
            first_of_month = (today.replace(day=1) - timedelta(days=30 * i))
            next_month = (first_of_month + timedelta(days=32)).replace(day=1)
            month_str = first_of_month.strftime("%Y-%m")

            params = {
                "app_id": self.adzuna_app_id,
                "app_key": self.adzuna_app_key,
                "what": job_title,
                "where": location,
                "results_per_page": 1,
                "distance": radius_km,
                "date_posted_min": first_of_month.isoformat(),
                "date_posted_max": next_month.isoformat(),
            }

            try:
                print(f"Querying Adzuna for month {month_str} with params: {params}")
                res = requests.get(base_url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    count = data.get("count", 0)
                    print(f"Month {month_str}: {count} jobs")
                    monthly_counts.append({"month": month_str, "count": count})
                else:
                    print(f"⚠️ Adzuna API error: {res.status_code} - {res.text}")
                    monthly_counts.append({"month": month_str, "count": 0})
            except Exception as e:
                print(f"🔥 Exception querying Adzuna: {e}")
                monthly_counts.append({"month": month_str, "count": 0})

        return monthly_counts

    def generate_interview_questions(self, skills, job_title):
        prompt = (
            f"Generate 10 interview questions a candidate should prepare for a job titled '{job_title}', "
            f"based on these skills: {skills}."
        )
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )
        questions_text = response.choices[0].message.content.strip()
        questions = [q.strip() for q in questions_text.split("\n") if q.strip()]
        return questions[:10]

    def register(self, request):
        try:
            data = request.get_json()
            name = data.get("name")
            email = data.get("email")
            skills = data.get("skills")
            location = data.get("location")
            summary = data.get("summary")
            radius_km = data.get("radius_km", 50)  # default radius 50 km if not provided

            # Validate required fields
            if not email or not name or not skills or not location or not summary:
                return jsonify({
                    "success": False,
                    "error": "Email, name, skills, location, and summary are required."
                }), 400

            client = get_gspread_client()

            # USERS SHEET
            users_sheet = client.open_by_key(os.getenv("USERS_SHEET_ID")).sheet1
            users = users_sheet.get_all_records()

            # Check if email exists
            if any(row["Email"] == email for row in users):
                return jsonify({"success": False, "error": "Email already registered."}), 400

            # Append new user (password handled elsewhere)
            users_sheet.append_row([email, "", ""])
            print(f"✅ Registered user: {email} in USERS sheet")

            # Extract job title using AI
            combined_text = f"{skills} {summary}"
            job_title = self.extract_job_title(combined_text)
            print(f"🧠 AI-derived job title: {job_title}")

            # Query job counts on Adzuna with radius
            job_count = self.query_adzuna_job_counts(job_title, location, radius_km=radius_km)
            print(f"📊 Jobs found for '{job_title}' near '{location}' within {radius_km} km: {job_count}")

            # Get monthly job counts for the last 6 months
            job_counts_over_time = self.get_job_counts_over_time(job_title, location, radius_km=radius_km, months=6)

            # Generate interview questions
            interview_questions = self.generate_interview_questions(skills, job_title)
            print(f"❓ Interview questions generated")

            # Append candidate info with new fields
            candidates_sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
            timestamp = datetime.now().isoformat()
            candidates_sheet.append_row([
                email, name, skills, location, summary, job_title, job_count,
                "\n".join(interview_questions), timestamp
            ])
            print(f"✅ Created profile for: {email} with job title and interview questions")

            dashboard_link = f"https://ai-talent-marketplace.onrender.com/dashboard"
            return jsonify({
                "success": True,
                "message": "Registration successful.",
                "job_title": job_title,
                "job_count": job_count,
                "job_counts_over_time": job_counts_over_time,
                "interview_questions": interview_questions,
                "dashboard_link": dashboard_link
            })

        except Exception as e:
            print(f"🔥 Error in register_user: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
