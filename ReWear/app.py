from flask import Flask, render_template, request, redirect, flash, url_for, session, flash
from database import create_user, get_user_by_email, SessionLocal, User
import bcrypt
import os
import secrets
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecret")

# === Email sender ===
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


def send_recovery_email(to_email, code):
    msg = EmailMessage()
    msg["Subject"] = "ReWear Password Reset Code"
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg.set_content(f"Your ReWear recovery code is: {code}")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)

# Home page
@app.route("/")
def index():
    return render_template("index.html")


# Sign Up
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = bcrypt.hashpw(request.form["password"].encode(), bcrypt.gensalt()).decode()
        uid = create_user(name, email, password)
        if uid:
            flash("Signup successful! Please login.")
            return redirect("/login")
        else:
            flash("Email already exists!")
    return render_template("signup.html")


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = get_user_by_email(email)
        if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
            session["uid"] = user["uid"]
            session["name"] = user["name"]
            return redirect("/")
        else:
            flash("Invalid email or password!")
    return render_template("login.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()
        if user:
            code = secrets.token_hex(3).upper()
            user.forgot_pass_code = code
            db.commit()

            send_recovery_email(email, code)
            flash("Reset code sent to your email.", "success")
            return redirect("/reset-password")
        else:
            flash("Email not found.", "danger")
    return render_template("forgot_password.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form["email"]
        code = request.form["code"]
        new_password = request.form["new_password"]
        db = SessionLocal()
        user = db.query(User).filter(User.email == email, User.forgot_pass_code == code).first()
        if user:
            hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            user.password = hashed
            user.forgot_pass_code = None
            db.commit()
            flash("Password reset successful. Please login.", "success")
            return redirect("/login")
        else:
            flash("Invalid email or code!", "danger")
    return render_template("reset_password.html")


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
