from flask import Flask, render_template, request, redirect, session, url_for, flash
from database import create_user, get_user_by_email, SessionLocal, User
import bcrypt
import secrets
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecret")

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


# Forgot password
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()
        if user:
            code = secrets.token_hex(4)
            user.forgot_pass_code = code
            db.commit()
            flash(f"Reset Code: {code} (showing here for demo)")
            return redirect("/reset-password")
        else:
            flash("Email not found!")
    return render_template("forgot_password.html")


# Reset password
@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form["email"]
        code = request.form["code"]
        new_password = request.form["new_password"]
        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()
        if user and user.forgot_pass_code == code:
            hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            user.password = hashed
            user.forgot_pass_code = None
            db.commit()
            flash("Password reset successful!")
            return redirect("/login")
        else:
            flash("Invalid email or code!")
    return render_template("reset_password.html")


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
