from flask import render_template, request, redirect, url_for, session, flash
from app import app
from app.models.user import User 
from .decorators import login_required
import logging
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from app.models.car import Car
from app.models.permit import Permit
from app.models.payment import Payment
from app.models.admin import Admin
from app.models.user import User
from flask import jsonify
import qrcode
from io import BytesIO
from flask import send_file
import barcode
from barcode.writer import ImageWriter
from werkzeug.security import generate_password_hash, check_password_hash 
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_type = request.form.get("user_type")
        email = request.form.get("email").strip()
        password = request.form.get("password").strip()
        user = None

        # Check user type and fetch the user by email
        if user_type == "user":
            user = User.get_by_email(email)
        elif user_type == "admin":
            user = Admin.get_by_email(email)
        if not user:
            flash("Email not found", "error")
            return render_template('login.html')

        # Check if the password is valid
        is_valid_password = False
        if user_type == "user":
            is_valid_password = User.check_password(user, password)
        elif user_type == "admin":
            is_valid_password = Admin.check_password(user, password)

        if not is_valid_password:
            flash("Invalid credentials", "error")
            return render_template('login.html')

        # Set user session details
        session["user_id"] = str(user["_id"])
        session["user_type"] = user_type

        if user_type == "user":
            return redirect(url_for('user_dashboard'))
        # Redirect to the appropriate dashboard after successful login
        elif user_type == "user":
            return redirect(url_for('user_dashboard'))
        elif user_type == "admin":
            return redirect(url_for('admin_dashboard'))

    return render_template('login.html')


@app.route('/sso_login', methods=['GET', 'POST'])
def sso_login():
    if request.method == 'POST':
        email = request.form.get("email").strip()
        password = request.form.get("password").strip()

        # Simulate DB lookup (replace this with actual DB call)
        user = User.find_one({"email": email})

        if user and password == user.get("password"):  # Password check
            # Store user details in session
            session['user_id'] = str(user["_id"])
            session['email'] = user["email"]
            session['role'] = user["role"]
            flash("SSO Login Successful!", "success")

            logger.info(f"User {email} logged in via SSO")


            # based on role student faculty police sodexo staff go to those dashboards respectively
            if user["role"] == "student" or user["role"] == "faculty" or user["role"] == "staff":
                return redirect(url_for('user_dashboard'))
            elif user["role"] == "police":
                return redirect(url_for('police_dashboard'))
            elif user["role"] == "sodexo":
                return redirect(url_for('sodexo_dashboard')) 
            else:
                flash("Invalid credentials for SSO login.", "error")
                return render_template('sso_login.html')

        flash("Invalid credentials for SSO login.", "error")
        return render_template('sso_login.html')

    return render_template('sso_login.html')  # Render SSO login page



@app.route('/user_get_permit')
def user_get_permit():
    # Check if user is logged in
    if 'user_id' not in session:
        flash("You must be logged in to access this page.", "error")
        return redirect(url_for('sso_login'))
    
    # Redirect to respective dashboard based on role
    role = session.get('role')
    
    if role == "student" or role == "faculty":
        return redirect(url_for('user_dashboard'))
    elif role == "police":
        return redirect(url_for('police_dashboard'))
    elif role == "sodexo":
        return redirect(url_for('sodexo_dashboard'))
    elif role == "staff":
        return redirect(url_for('staff_dashboard'))
    else:
        flash("Invalid role. Please contact support.", "error")
        return redirect(url_for('sso_login'))





# register admin secret url
@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    try:
        if request.method == 'POST':
            email = request.form.get("email").strip()
            if Admin.exists_by_email(email):
                return "Email already registered", 400

            password = request.form.get("password").strip()
            confirm_password = request.form.get("confirm_password").strip()

            if password != confirm_password:
                return "Passwords do not match", 400

            data = {
                "user_name": request.form.get("user_name").strip(), 
                "email": email,
                "password": password
            }
            Admin.create(data)
            return redirect(url_for('admin_login'))

        return render_template('admin/register_admin.html')
    except Exception as e:
        logger.error(f"Error during admin registration: {str(e)}")
        return "Internal Server Error", 500
    

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get("email").strip()
        password = request.form.get("password").strip()

        # Fetch admin user by email
        admin = Admin.get_by_email(email)
        
        if not admin:
            flash("Email not found", "error")
            return render_template('admin/login.html')

        # Check plain password
        if admin.get("password") != password:  # Plain text comparison
            flash("Invalid credentials", "error")
            return render_template('admin/login.html')

        # Set session and login success
        session["user_id"] = str(admin["_id"])
        session["email"] = admin["email"]
        session["role"] = "admin"
        flash("Login successful!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/login.html')








# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('sso_login'))


@app.route('/guest_login', methods=['GET'])
def guest_login():
    return render_template('guest_login.html')

# Example: Route for guest login processing
@app.route('/guest_login', methods=['POST'])
def guest_login_post():
    email = request.form.get('email')
    password = request.form.get('password')

    # Check email and password here (add actual validation logic)
    if email == "guest@example.com" and password == "password":
        session['user'] = email
        flash("Login successful!", "success")
        return redirect(url_for('guest_dashboard'))
    else:
        flash("Invalid credentials!", "error")
        return redirect(url_for('guest_login'))

# Guest Dashboard Route
@app.route('/guest_dashboard')
def guest_dashboard():
    if "user" not in session:
        return redirect(url_for('guest_login'))
    return "Welcome to the Guest Dashboard"
