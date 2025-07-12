from datetime import datetime
import bcrypt
from flask import Flask, render_template, request, redirect, flash, url_for, session, flash, abort
from database import Transaction, create_user, get_user_by_email, SessionLocal, User, get_available_products,SessionLocal, User, Product
import os
import secrets
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from functools import wraps
from sqlalchemy.orm import joinedload

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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        uid = session.get("uid")
        if not uid:
            flash("Login required", "warning")
            return redirect(url_for("login"))

        db = SessionLocal()
        user = db.query(User).filter_by(uid=uid).first()
        db.close()
        if not user or user.role != "admin":
            flash("Access denied: Admins only", "danger")
            return redirect(url_for("landing_page"))
        return f(*args, **kwargs)
    return decorated_function


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "uid" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def index():
    return render_template("index.html")  # Show about, login, signup buttons

@app.route("/admin")
@login_required
def admin_panel():
    db = SessionLocal()
    
    current_user = db.query(User).filter(User.uid == session["uid"]).first()
    if not current_user or current_user.role != "admin":
        flash("Access denied: Admins only", "danger")
        return redirect(url_for("landing_page"))

    users = db.query(User).all()
    transactions = db.query(Transaction).all()
    products = db.query(Product).options(joinedload(Product.images)).all()

    return render_template("admin_panel.html", 
                           users=users,
                           transactions=transactions,
                           products=products,
                           current_user=current_user)

@app.route("/home")
@login_required
def landing_page():
    now = datetime.now()
    db = SessionLocal()

    # Fetch products with related images
    products = db.query(Product).options(joinedload(Product.images)).filter(
        Product.status == "available"
    ).order_by(Product.created_at.desc()).limit(4).all()
    return render_template(
        "landing_page.html",
        products=products,
        now=now
    )

@app.route("/product/<int:pid>")
def product_detail(pid):
    db = SessionLocal()
    product = db.query(Product).filter(Product.pid == pid).first()
    if not product:
        abort(404)
    images = sorted(product.images, key=lambda i: not i.is_primary)
    now = datetime.now()
    return render_template("product_detail.html", product=product, images=images, now = now)

@app.route("/my-orders")
@login_required
def my_orders():
    db = SessionLocal()
    uid = session.get("uid")

    # All swaps involving the current user
    all_swaps = db.query(Transaction).filter(
        (Transaction.requester.has(uid=uid)) |
        (Transaction.receiver.has(uid=uid))
    ).order_by(Transaction.created_at.desc()).all()

    # Sent swaps (where user is requester)
    sent_swaps = db.query(Transaction).filter(
        Transaction.requester.has(uid=uid)
    ).order_by(Transaction.created_at.desc()).all()

    # Received swaps (where user is receiver)
    received_swaps = db.query(Transaction).filter(
        Transaction.receiver.has(uid=uid)
    ).order_by(Transaction.created_at.desc()).all()

    # Completed swaps (status = 'completed')
    completed_swaps = db.query(Transaction).filter(
        ((Transaction.requester.has(uid=uid)) | (Transaction.receiver.has(uid=uid))) &
        (Transaction.status == 'completed')
    ).order_by(Transaction.created_at.desc()).all()

    now = datetime.now()

    return render_template(
        "my_orders.html",
        all_swaps=all_swaps,
        sent_swaps=sent_swaps,
        received_swaps=received_swaps,
        completed_swaps=completed_swaps,
        now=now
    )


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
            return redirect("/home")
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


# Route to display profile page
@app.route("/profile", methods=["GET"])
def profile():
    if "uid" not in session:
        flash("Please login to view your profile.")
        return redirect("/login")
    
    db = SessionLocal()
    user = db.query(User).filter(User.uid == session["uid"]).first()
    now = datetime.now()

    return render_template("profile.html", current_user=user, now=now)


# Route to update profile
@app.route("/update-profile", methods=["POST"])
def update_profile():
    if "uid" not in session:
        flash("Please login first.")
        return redirect("/login")

    db = SessionLocal()
    user = db.query(User).filter(User.uid == session["uid"]).first()

    # Get form fields
    user.fullname = request.form.get("fullname")
    user.gender = request.form.get("gender")
    user.phone = request.form.get("phone")
    user.address = request.form.get("address")
    user.city = request.form.get("city")
    user.state = request.form.get("state")
    user.zip = request.form.get("zip")
    user.country = request.form.get("country")

    db.commit()
    flash("Profile updated successfully.", "success")
    return redirect("/profile")

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
     app.run(host='0.0.0.0', port=5000, debug=True)

