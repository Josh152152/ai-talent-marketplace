import bcrypt
from flask import Blueprint, request, redirect, render_template
from sheets import get_gspread_client
import os

# Create Blueprint for authentication
auth = Blueprint("auth", __name__)

SHEET_NAME = "AI Talent Users"

# Function to retrieve a user by email from Google Sheets
def get_user_from_sheet(email):
    client = get_gspread_client()
    sheet = client.open(SHEET_NAME).sheet1
    users = sheet.get_all_records()

    for user in users:
        if user["Email"].strip().lower() == email.strip().lower():
            return user
    return None

# Function to add a new user to Google Sheets
def add_user_to_sheet(name, email, hashed_pwd, user_type, radius="50"):
    client = get_gspread_client()

    # Add to AI Talent Users sheet
    users_sheet = client.open(SHEET_NAME).sheet1
    users_sheet.append_row([name, email, hashed_pwd.decode("utf-8"), user_type])
    print(f"✅ Added user to {SHEET_NAME}")

    # If the user is a candidate, add a stub row to the Candidates sheet
    if user_type.strip().lower() == "candidate":
        sheet_id = os.getenv("CANDIDATES_SHEET_ID")
        print(f"📄 DEBUG: CANDIDATES_SHEET_ID = {sheet_id}")

        if not sheet_id:
            raise ValueError("❌ Environment variable CANDIDATES_SHEET_ID is missing.")

        try:
            candidates_sheet = client.open_by_key(sheet_id).sheet1
            new_row = [""] * 11
            new_row[0] = email
            new_row[1] = name
            new_row[10] = radius  # Radius always in column K
            candidates_sheet.append_row(new_row)
            print(f"✅ Stub row added to Candidates sheet for {email}")
        except Exception as e:
            print(f"🔥 Failed to write to Candidates sheet: {e}")
            raise

# Route for signup page (GET and POST methods)
@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    user_type = request.form.get("type", "").strip()

    # Check for missing fields
    if not name or not email or not password or not user_type:
        return "Missing fields", 400

    # Check if the user already exists
    if get_user_from_sheet(email):
        return "User already exists", 400

    # Hash the password
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    try:
        print(f"🔐 Registering user: {email}")
        add_user_to_sheet(name, email, hashed, user_type)
    except Exception as e:
        print(f"🔥 Error during signup/add_user_to_sheet: {e}")
        return f"Internal server error: {str(e)}", 500

    # Redirect to login after successful signup
    return redirect("/auth/login")

# Route for login page (GET and POST methods)
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    # Debugging print to check the form input
    print(f"Login attempt with email: {email} and password: {password}")

    user = get_user_from_sheet(email)
    if not user:
        return "Invalid credentials", 401

    stored_hash = user["Password_Hash"].encode("utf-8")
    if not bcrypt.checkpw(password.encode("utf-8"), stored_hash):
        return "Invalid credentials", 401

    # Debugging to check the user type
    print(f"User {email} of type {user['Type']} logged in.")

    # Redirect to the appropriate dashboard based on user type
    if user["Type"].strip().lower() == "candidate":
        return redirect(f"/dashboard?email={email}")
    else:
        return redirect("/employer_dashboard")
