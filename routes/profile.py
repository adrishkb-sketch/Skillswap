from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
profile_bp = Blueprint('profile', __name__)

import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "static/uploads/profile_pics"

@profile_bp.route("/complete-profile", methods=["GET", "POST"])
@login_required
def complete_profile():
    if request.method == "POST":
        current_user.full_name = request.form.get("full_name")
        current_user.college = request.form.get("college")
        current_user.degree = request.form.get("degree")
        current_user.bio = request.form.get("bio")
        current_user.skills_teach = request.form.get("skills_teach")
        current_user.skills_learn = request.form.get("skills_learn")

        profile_pic = request.files.get("profile_pic")

        if profile_pic and profile_pic.filename != "":
            filename = secure_filename(profile_pic.filename)

            # Create folder if not exists
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            file_path = os.path.join(UPLOAD_FOLDER, filename)
            profile_pic.save(file_path)

            current_user.profile_pic = file_path

        current_user.is_profile_complete = True
        db.session.commit()

        return redirect(url_for("dashboard.dashboard_home"))

    return render_template("complete_profile.html")
@profile_bp.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():

    if request.method == "POST":
        current_user.full_name = request.form.get("full_name")
        current_user.bio = request.form.get("bio")
        current_user.skills_teach = request.form.get("skills_teach")
        current_user.skills_learn = request.form.get("skills_learn")

        db.session.commit()

        return redirect(url_for("dashboard.dashboard_home"))

    return render_template("complete_profile.html")