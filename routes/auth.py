from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import User, OTPVerification
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user
import random
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


# -----------------------------------
# Landing Page
# -----------------------------------
@auth_bp.route("/")
def landing():
    return render_template("landing.html")


# -----------------------------------
# Register
# -----------------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered.")
            return redirect(url_for("auth.register"))

        # Generate OTP
        otp = str(random.randint(100000, 999999))

        # Hash password
        hashed_password = generate_password_hash(password)

        # Store OTP + hashed password
        otp_entry = OTPVerification(
            email=email,
            otp=otp,
            password=hashed_password
        )

        db.session.add(otp_entry)
        db.session.commit()

        # For now: print OTP in terminal (we connect real email later)
        print(f"\n🔐 OTP for {email} is: {otp}\n")

        flash("OTP sent to your email.")
        return redirect(url_for("auth.verify_otp", email=email))

    return render_template("register.html")


# -----------------------------------
# Verify OTP
# -----------------------------------
@auth_bp.route("/verify/<email>", methods=["GET", "POST"])
def verify_otp(email):
    if request.method == "POST":
        entered_otp = request.form.get("otp")

        # Get latest OTP entry for this email
        otp_record = OTPVerification.query.filter_by(email=email).order_by(
            OTPVerification.created_at.desc()
        ).first()

        if otp_record and otp_record.otp == entered_otp:

            # Create new user using stored hashed password
            new_user = User(
                email=email,
                password=otp_record.password
            )

            db.session.add(new_user)

            # Delete OTP record
            db.session.delete(otp_record)

            db.session.commit()

            flash("Account created successfully. Please login.")
            return redirect(url_for("auth.login"))

        else:
            flash("Invalid OTP. Try again.")

    return render_template("verify_otp.html", email=email)


# -----------------------------------
# Login
# -----------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)

            # If profile not complete → force completion
            if not user.is_profile_complete:
                return redirect(url_for("profile.complete_profile"))

            return redirect(url_for("dashboard.dashboard_home"))

        flash("Invalid email or password.")

    return render_template("login.html")


# -----------------------------------
# Logout
# -----------------------------------
@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.landing"))