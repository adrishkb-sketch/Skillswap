from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Course, CourseSection, MCQ, SectionCompletion, Certificate
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

        new_course = Course(
            title=request.form.get("title"),
            description=request.form.get("description"),
            tags=request.form.get("tags"),
            credits_required=request.form.get("credits_required"),
            instructor_id=current_user.id
        )

        db.session.add(new_course)
        db.session.commit()

        # Redirect to builder
        return redirect(f"/course/{new_course.id}/builder")

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

@courses_bp.route("/course/<int:course_id>", methods=["GET", "POST"])
@login_required
def view_course(course_id):

    course = Course.query.get_or_404(course_id)

    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=course_id
    ).first()

    if not enrollment and course.instructor_id != current_user.id:
        return redirect(url_for("dashboard.dashboard_home"))

    # 🔥 FETCH SECTIONS PROPERLY
    sections = CourseSection.query.filter_by(
        course_id=course_id
    ).order_by(CourseSection.order).all()

    return render_template(
        "course_view.html",
        course=course,
        sections=sections
    )
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

@courses_bp.route("/course/<int:course_id>/builder")
@login_required
def course_builder(course_id):
    course = Course.query.get_or_404(course_id)

    if course.instructor_id != current_user.id:
        return redirect("/dashboard")

    sections = CourseSection.query.filter_by(
        course_id=course_id
    ).order_by(CourseSection.order).all()

    return render_template(
        "course_builder.html",
        course=course,
        sections=sections
    )
from flask import current_app, request, redirect
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from extensions import db
from models import Course, CourseSection



@courses_bp.route("/course/<int:course_id>/add-section", methods=["POST"])
@login_required
def add_section(course_id):

    # Get course
    course = Course.query.get_or_404(course_id)

    # Only instructor can modify
    if course.instructor_id != current_user.id:
        return redirect("/dashboard")

    title = request.form.get("title")
    content_type = request.form.get("content_type")

    # Determine next order number
    section_count = CourseSection.query.filter_by(
        course_id=course_id
    ).count()

    new_section = CourseSection(
        title=title,
        content_type=content_type,
        order=section_count + 1,
        course_id=course_id
    )

    upload_folder = current_app.config["UPLOAD_FOLDER"]

    # ---------------- VIDEO ----------------
    if content_type == "video":
        video = request.files.get("video")

        if video and video.filename != "":
            filename = secure_filename(video.filename)
            file_path = os.path.join(upload_folder, filename)
            video.save(file_path)

            # Save relative path
            new_section.video_path = f"uploads/{filename}"

    # ---------------- DOCUMENT ----------------
    if content_type == "document":
        document = request.files.get("document")

        if document and document.filename != "":
            filename = secure_filename(document.filename)
            file_path = os.path.join(upload_folder, filename)
            document.save(file_path)

            new_section.document_path = f"uploads/{filename}"

    # ---------------- QUIZ ----------------
    # For quiz type, no file upload needed
    # MCQs will be added later

    db.session.add(new_section)
    db.session.commit()
    # Credit reward logic
    if content_type == "video":
        course_owner = current_user
        course_owner.credits += 10

    elif content_type == "document":
        course_owner = current_user
        course_owner.credits += 5

    elif content_type == "quiz":
        course_owner = current_user
        course_owner.credits += 3

    db.session.commit()

    return redirect(f"/course/{course_id}/builder")

@courses_bp.route("/section/<int:section_id>/add-mcq", methods=["POST"])
@login_required
def add_mcq(section_id):

    section = CourseSection.query.get_or_404(section_id)

    if section.content_type != "quiz":
        return redirect(request.referrer)

    question = request.form.get("question")
    option_a = request.form.get("option_a")
    option_b = request.form.get("option_b")
    option_c = request.form.get("option_c")
    option_d = request.form.get("option_d")
    correct_answer = request.form.get("correct_answer")

    new_mcq = MCQ(
        question=question,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_answer=correct_answer,
        section_id=section_id
    )

    db.session.add(new_mcq)
    db.session.commit()
    current_user.credits += 1
    db.session.commit()
    return redirect(request.referrer)

@courses_bp.route("/section/<int:section_id>/complete")
@login_required
def complete_section(section_id):

    # Get section
    section = CourseSection.query.get_or_404(section_id)
    course_id = section.course_id
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=section.course_id
    ).first()

    if not enrollment:
        return redirect("/dashboard")
    # Check if already completed
    existing = SectionCompletion.query.filter_by(
        student_id=current_user.id,
        section_id=section_id
    ).first()

    if not existing:
        completion = SectionCompletion(
            student_id=current_user.id,
            section_id=section_id,
            completed=True
        )
        db.session.add(completion)
        db.session.commit()

    # ---- CERTIFICATE CHECK ----

    total_sections = CourseSection.query.filter_by(
        course_id=course_id
    ).count()

    completed_sections = SectionCompletion.query.join(
        CourseSection
    ).filter(
        SectionCompletion.student_id == current_user.id,
        CourseSection.course_id == course_id
    ).count()

    if total_sections > 0 and total_sections == completed_sections:

        existing_certificate = Certificate.query.filter_by(
            user_id=current_user.id,
            course_id=course_id
        ).first()

        if not existing_certificate:
            new_certificate = Certificate(
                user_id=current_user.id,
                course_id=course_id
            )
            db.session.add(new_certificate)
            db.session.commit()

    return redirect(request.referrer)

@courses_bp.route("/section/<int:section_id>/move-up")
@login_required
def move_up(section_id):

    section = CourseSection.query.get_or_404(section_id)

    previous = CourseSection.query.filter_by(
        course_id=section.course_id,
        order=section.order - 1
    ).first()

    if previous:
        section.order, previous.order = previous.order, section.order
        db.session.commit()

    return redirect(request.referrer)


@courses_bp.route("/section/<int:section_id>/move-down")
@login_required
def move_down(section_id):

    section = CourseSection.query.get_or_404(section_id)

    next_section = CourseSection.query.filter_by(
        course_id=section.course_id,
        order=section.order + 1
    ).first()

    if next_section:
        section.order, next_section.order = next_section.order, section.order
        db.session.commit()

    return redirect(request.referrer)

@courses_bp.route("/section/<int:section_id>/edit",
                  methods=["POST"])
@login_required
def edit_section(section_id):

    section = CourseSection.query.get_or_404(section_id)

    section.title = request.form.get("title")
    db.session.commit()

    return redirect(request.referrer)

@courses_bp.route("/section/<int:section_id>/delete")
@login_required
def delete_section(section_id):

    section = CourseSection.query.get_or_404(section_id)

    # Ensure only instructor deletes
    course = Course.query.get(section.course_id)
    if course.instructor_id != current_user.id:
        return redirect("/dashboard")

    # Delete associated MCQs
    MCQ.query.filter_by(section_id=section_id).delete()

    db.session.delete(section)
    db.session.commit()

    # Reorder remaining sections
    sections = CourseSection.query.filter_by(
        course_id=course.id
    ).order_by(CourseSection.order).all()

    for index, sec in enumerate(sections):
        sec.order = index + 1

    db.session.commit()

    return redirect(f"/course/{course.id}/builder")

@courses_bp.route("/mcq/<int:mcq_id>/delete")
@login_required
def delete_mcq(mcq_id):

    mcq = MCQ.query.get_or_404(mcq_id)
    section_id = mcq.section_id

    db.session.delete(mcq)
    db.session.commit()

    return redirect(request.referrer)