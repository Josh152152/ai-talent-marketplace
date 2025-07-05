import bcrypt
from flask import Blueprint, request, redirect, render_template
from sheets import get_gspread_client
import os

auth = Blueprint("auth", __name__)

SHEET_NAME = "AI Talent Users"

def get_user_from_sheet(email):
    client = get_gspread_client()
    sheet = client.open(SHEET_NAME).sheet1
    users = sheet.get_all_records()

    for user in users:
        if user["Email"].strip().lower() == email.strip().lower():
            return user
    return None

def add_user_to_sheet(name, email, hashed_pwd, user_type):
    client = get_gspread_client()

    # Add to AI Talent Users sheet (columns: Name, Email, Password_Hash, Type)
    users_sheet = client.open(SHEET_NAME).sheet1
    users_sheet.append_row(
        [name, email, hashed_pwd.decode("utf-8"), user_type],
        value_input_option="USER_ENTERED"
    )

    # Add to Candidates sheet if Candidate
    if user_type.strip().lower() == "candidate":
        candidates_sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1

        # Ensure 11 columns, exactly in the right order:
        # [Email, Name, Skills, Location, Summary, Job Title, Job Count, Interview Questions, Embedding, Timestamp, Radius]
        new_row = [
            email,         # A
            name,          # B
            "",            # C
            "",            # D
            "",            # E
            "",            # F
            "",            # G
            "",            # H
            "",            # I
            "",            # J
            "50"           # K (Radius)
        ]

        # This ensures no column shifting/misalignment
        candidates_sheet.append_row(new_row, value_input_option="USER_ENTERED")

@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    user_type = request.form.get("type")

    if not name or not email or not password or not user_type:
        return "Missing fields", 400

    if get_user_from_sheet(email):
        return "User already exists", 400

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    add_user_to_sheet(name, email, hashed, user_type)

    return redirect("/login")

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")

    user = get_user_from_sheet(email)
    if not user:
        return "Invalid credentials", 401

    stored_hash = user["Password_Hash"].encode("utf-8")
    if not bcrypt.checkpw(password.encode("utf-8"), stored_hash):
        return "Invalid credentials", 401

    if user["Type"].strip().lower() == "candidate":
        return redirect(f"/dashboard?email={email}")
    else:
        return redirect("/employer_dashboard")
