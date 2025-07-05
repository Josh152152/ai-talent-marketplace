import bcrypt
from flask import Blueprint, request, redirect, render_template
from sheets import get_gspread_client
import os

auth = Blueprint("auth", __name__)

USERS_SHEET = "AI Talent Users"
CANDIDATE_SHEET_ID = os.getenv("CANDIDATES_SHEET_ID")  # must be in .env

def get_user_from_sheet(email):
    client = get_gspread_client()
    sheet = client.open(USERS_SHEET).sheet1
    users = sheet.get_all_records()

    for user in users:
        if user["Email"].strip().lower() == email.strip().lower():
            return user
    return None

def add_user_to_sheet(name, email, hashed_pwd, user_type):
    client = get_gspread_client()
    sheet = client.open(USERS_SHEET).sheet1
    sheet.append_row([name, email, hashed_pwd.decode("utf-8"), user_type])

def create_candidate_profile_if_needed(name, email):
    client = get_gspread_client()
    sheet = client.open_by_key(CANDIDATE_SHEET_ID).sheet1
    records = sheet.get_all_records()

    already_exists = any(row.get("Email", "").strip().lower() == email.strip().lower() for row in records)
    if not already_exists:
        sheet.append_row([
            name,         # Name
            "",           # Placeholder for whatever column 2 is
            "",           # Skills
            "",           # Location
            "",           # Summary
            "", "", "", "", "", "", "",  # more columns if needed
            "",           # Radius (col 13)
            email         # Email
        ])

@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    name = request.form.get("name")
    email = request.form.get("email").strip().lower()
    password = request.form.get("password")
    user_type = request.form.get("type")

    if not name or not email or not password or not user_type:
        return "Missing fields", 400

    if get_user_from_sheet(email):
        return "User already exists", 400

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    add_user_to_sheet(name, email, hashed, user_type)

    if user_type.lower() == "candidate":
        create_candidate_profile_if_needed(name, email)

    return redirect("/login")

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email").strip().lower()
    password = request.form.get("password")

    user = get_user_from_sheet(email)
    if not user:
        return "Invalid credentials", 401

    stored_hash = user["Password_Hash"].encode("utf-8")
    if not bcrypt.checkpw(password.encode("utf-8"), stored_hash):
        return "Invalid credentials", 401

    # Redirect by role
    if user["Type"] == "Candidate":
        return redirect(f"/dashboard?email={email}")
    else:
        return redirect("/employer_dashboard")
