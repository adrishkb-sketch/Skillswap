from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Course
from werkzeug.utils import secure_filename
import os
from models import User
courses_bp = Blueprint('courses', __name__)

VIDEO_FOLDER = "static/uploads/course_videos"
DOC_FOLDER = "static/uploads/course_docs"


@courses_bp.route("/create-course", methods=["GET", "POST"])
@login_required
def create_course():
    if request.method == "POST":

        title = request.form.get("title")
        description = request.form.get("description")
        tags = request.form.get("tags")
        duration = int(request.form.get("duration"))

        # Auto credit calculation
        credits_required = duration // 10 + 5   # simple logic

        video = request.files.get("video")
        document = request.files.get("document")

        os.makedirs(VIDEO_FOLDER, exist_ok=True)
        os.makedirs(DOC_FOLDER, exist_ok=True)

        video_path = None
        doc_path = None

        if video and video.filename != "":
            filename = secure_filename(video.filename)
            video_path = os.path.join(VIDEO_FOLDER, filename)
            video.save(video_path)

        if document and document.filename != "":
            filename = secure_filename(document.filename)
            doc_path = os.path.join(DOC_FOLDER, filename)
            document.save(doc_path)

        new_course = Course(
            title=title,
            description=description,
            tags=tags,
            duration=duration,
            credits_required=credits_required,
            video_path=video_path,
            document_path=doc_path,
            instructor_id=current_user.id
        )

        db.session.add(new_course)

        # Instructor earns credits for uploading
        current_user.credits += credits_required // 2

        db.session.commit()

        return redirect(url_for("dashboard.dashboard_home"))

    return render_template("create_course.html")

from models import Enrollment, CreditTransaction, PlatformWallet


@courses_bp.route("/enroll/<int:course_id>")
@login_required
def enroll_course(course_id):

    course = Course.query.get_or_404(course_id)

    # Prevent enrolling in own course
    if course.instructor_id == current_user.id:
        return redirect(url_for("dashboard.dashboard_home"))

    # Check if already enrolled
    existing = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=course_id
    ).first()

    if existing:
        return redirect(url_for("dashboard.dashboard_home"))

    # Check if enough credits
    if current_user.credits < course.credits_required:
        return redirect(url_for("dashboard.dashboard_home"))

    # Deduct credits from student
    current_user.credits -= course.credits_required

    # 75% to instructor
    instructor_share = int(course.credits_required * 0.75)

    instructor = User.query.get(course.instructor_id)
    instructor.credits += instructor_share

    # 25% to platform
    platform_share = course.credits_required - instructor_share

    wallet = PlatformWallet.query.first()
    if not wallet:
        wallet = PlatformWallet(total_credits=0)
        db.session.add(wallet)

    wallet.total_credits += platform_share

    # Create enrollment
    enrollment = Enrollment(
        student_id=current_user.id,
        course_id=course_id
    )

    db.session.add(enrollment)

    # Log transactions
    db.session.add(CreditTransaction(
        user_id=current_user.id,
        amount=-course.credits_required,
        type="spend"
    ))

    db.session.add(CreditTransaction(
        user_id=instructor.id,
        amount=instructor_share,
        type="earn"
    ))

    db.session.commit()

    return redirect(url_for("dashboard.dashboard_home"))

@courses_bp.route("/course/<int:course_id>")
@login_required
def view_course(course_id):

    course = Course.query.get_or_404(course_id)

    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=course_id
    ).first()

    if not enrollment and course.instructor_id != current_user.id:
        return redirect(url_for("dashboard.dashboard_home"))

    return render_template("course_view.html", course=course)

from models import Review

@courses_bp.route("/review/<int:course_id>", methods=["POST"])
@login_required
def add_review(course_id):

    rating = int(request.form.get("rating"))
    comment = request.form.get("comment")

    new_review = Review(
        student_id=current_user.id,
        course_id=course_id,
        rating=rating,
        comment=comment
    )

    db.session.add(new_review)
    db.session.commit()

    return redirect(url_for("courses.view_course", course_id=course_id))

from models import Certificate
import uuid
from reportlab.pdfgen import canvas

@courses_bp.route("/complete/<int:course_id>")
@login_required
def complete_course(course_id):

    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=course_id
    ).first()

    if not enrollment:
        return redirect(url_for("dashboard.dashboard_home"))

    enrollment.completed = True

    certificate_id = str(uuid.uuid4())

    new_cert = Certificate(
        user_id=current_user.id,
        course_id=course_id,
        certificate_id=certificate_id
    )

    db.session.add(new_cert)
    db.session.commit()

    # Generate PDF
    file_path = f"static/certificates/{certificate_id}.pdf"
    os.makedirs("static/certificates", exist_ok=True)

    c = canvas.Canvas(file_path)
    c.drawString(100, 750, "SkillSwap Certificate of Completion")
    c.drawString(100, 720, f"Certificate ID: {certificate_id}")
    c.drawString(100, 690, f"Course ID: {course_id}")
    c.save()

    return redirect(url_for("courses.view_course", course_id=course_id))