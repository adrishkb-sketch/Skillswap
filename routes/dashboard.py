from flask import Blueprint, render_template
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard', __name__)


from models import Course, Enrollment

@dashboard_bp.route("/dashboard")
@login_required
def dashboard_home():

    user_skills = current_user.skills_learn or ""
    skills_list = [skill.strip().lower() for skill in user_skills.split(",") if skill]

    all_courses = Course.query.all()

    matched_courses = []
    my_courses = []
    enrolled_courses = []

    for course in all_courses:

        if course.instructor_id == current_user.id:
            my_courses.append(course)

        if skills_list:
            course_tags = (course.tags or "").lower()
            for skill in skills_list:
                if skill in course_tags:
                    matched_courses.append(course)
                    break

    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()

    for enrollment in enrollments:
        course = Course.query.get(enrollment.course_id)
        enrolled_courses.append(course)

    return render_template(
        "dashboard.html",
        user=current_user,
        courses=matched_courses,
        my_courses=my_courses,
        enrolled_courses=enrolled_courses
    )

from models import CreditTransaction

@dashboard_bp.route("/transactions")
@login_required
def transactions():

    user_transactions = CreditTransaction.query.filter_by(
        user_id=current_user.id
    ).order_by(CreditTransaction.timestamp.desc()).all()

    return render_template("transactions.html", transactions=user_transactions)