from flask import Flask, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re
from dotenv import load_dotenv
from pymongo import MongoClient
from functools import wraps
from datetime import datetime
import cloudinary
import cloudinary.uploader
import uuid
import qrcode
import base64
import io
from bson import ObjectId

load_dotenv()  # load .env file

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# MongoDB connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client["phr_db"]


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]

        if len(password) < 6:
            flash("Password must be at least 6 characters long.")
            return redirect(url_for("signup"))

        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_pattern, email):
            flash("Please enter a valid email address (e.g. name@example.com).")
            return redirect(url_for("signup"))

        existing_user = db.users.find_one({"email": email})
        if existing_user:
            flash("This email is already registered. Please login instead.")
            return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password)
        db.users.insert_one({
            "fullname": fullname,
            "email": email,
            "password": hashed_password,
            "share_token": uuid.uuid4().hex   # a random public ID for this user

        })

        return render_template("success.html", fullname=fullname)

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = db.users.find_one({"email": email})

        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["fullname"] = user["fullname"]
            flash(f"Welcome back, {user['fullname']}!")
            return redirect(url_for("home"))
        else:
            flash("Incorrect email or password.")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    return f"Welcome to your dashboard, {session['fullname']}!"


ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/add-visit", methods=["GET", "POST"])
@login_required
def add_visit():
    if request.method == "POST":
        visit_date = request.form["visit_date"]
        doctor_name = request.form["doctor_name"]
        diagnosis = request.form["diagnosis"]
        medicines = request.form["medicines"]
        advice = request.form["advice"]

        # --- Handle the uploaded file (optional) ---
        report_url = None
        file = request.files.get("report_file")

        if file and file.filename != "":
            if not allowed_file(file.filename):
                flash("Only PDF, JPG, and PNG files are allowed.")
                return redirect(url_for("add_visit"))

            file_ext = file.filename.rsplit(".", 1)[1].lower()
            resource_type = "image" if file_ext in {"jpg", "jpeg", "png"} else "raw"

            upload_result = cloudinary.uploader.upload(
                file,
                resource_type=resource_type,
                folder="phr_reports"
            )
            report_url = upload_result["secure_url"]

        db.visits.insert_one({
            "patient_id": session["user_id"],
            "visit_date": visit_date,
            "doctor_name": doctor_name,
            "diagnosis": diagnosis,
            "medicines": medicines,
            "advice": advice,
            "report_url": report_url,
            "created_at": datetime.utcnow()
        })

        flash("Visit record saved successfully.")
        return redirect(url_for("my_visits"))

    return render_template("add_visit.html")


@app.route("/my-visits")
@login_required
def my_visits():
    # Get search/filter values from the URL (e.g. ?doctor=Ahmed&condition=flu)
    doctor_query = request.args.get("doctor", "").strip()
    condition_query = request.args.get("condition", "").strip()
    date_query = request.args.get("date", "").strip()

    # Start with a filter that always applies: only this patient's visits
    filter_query = {"patient_id": session["user_id"]}

    # Add extra filters only if the user actually typed something
    if doctor_query:
        filter_query["doctor_name"] = {"$regex": doctor_query, "$options": "i"}

    if condition_query:
        filter_query["diagnosis"] = {"$regex": condition_query, "$options": "i"}

    if date_query:
        filter_query["visit_date"] = date_query

    # Sort by date, newest first
    visits = list(db.visits.find(filter_query).sort("visit_date", -1))

    return render_template(
        "my_visits.html",
        visits=visits,
        doctor_query=doctor_query,
        condition_query=condition_query,
        date_query=date_query
    )

@app.route("/share")
@login_required
def share():
    user = db.users.find_one({"_id": ObjectId(session["user_id"])})

    # If this user doesn't have a share_token yet (old account), create one now
    if "share_token" not in user or not user["share_token"]:
        new_token = uuid.uuid4().hex
        db.users.update_one(
            {"_id": ObjectId(session["user_id"])},
            {"$set": {"share_token": new_token}}
        )
        share_token = new_token
    else:
        share_token = user["share_token"]

    # Build the full public URL
    share_url = url_for("public_view", token=share_token, _external=True)

    # Generate a QR code image in memory (no file saved to disk)
    qr_img = qrcode.make(share_url)
    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return render_template("share.html", share_url=share_url, qr_base64=qr_base64)
@app.route("/view/<token>")
def public_view(token):
    user = db.users.find_one({"share_token": token})

    if not user:
        return "This link is invalid or has expired.", 404

    visits = list(db.visits.find({"patient_id": str(user["_id"])}))

    return render_template("public_view.html", patient=user, visits=visits)
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = db.users.find_one({"_id": ObjectId(session["user_id"])})

    if request.method == "POST":
        dob = request.form["dob"]
        address = request.form["address"]
        allergies = request.form["allergies"]
        current_medicines = request.form["current_medicines"]

        db.users.update_one(
            {"_id": ObjectId(session["user_id"])},
            {"$set": {
                "dob": dob,
                "address": address,
                "allergies": allergies,
                "current_medicines": current_medicines
            }}
        )

        flash("Profile updated successfully.")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)

@app.route("/db-test")
def db_test():
    try:
        client.admin.command("ping")
        return "MongoDB Atlas connected successfully!"
    except Exception as e:
        return f"Connection failed: {e}"


if __name__ == "__main__":
    app.run(debug=True)