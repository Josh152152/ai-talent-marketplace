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

    # Add to AI Talent Users sheet (ensure correct column order: Name, Email, Password_Hash, Type)
    users_sheet = client.open(SHEET_NAME).sheet1
    users_sheet.append_row([name, email, hashed_pwd.decode("utf-8"), user_type])

    # Also add to Candidates sheet if it's a candidate
    if user_type == "Candidate":
        candidate_sheet = client.open_by_key(os.getenv("CANDIDATES_SHEET_ID")).sheet1
        candidate_sheet.append_row([email, name, "", "", "", "", "", "", "", ""])

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

    # Redirect by role
    if user["Type"] == "Candidate":
        return redirect(f"/dashboard?email={email}")
    else:
        return redirect("/employer_dashboard")
