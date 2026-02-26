from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models import User, Course, Enrollment, CreditTransaction

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard_home():

    search_query = request.args.get("search")

    user_skills = current_user.skills_learn or ""
    skills_list = [skill.strip().lower() for skill in user_skills.split(",") if skill]

    all_courses = Course.query.all()

    matched_courses = []
    my_courses = []
    enrolled_courses = []

    for course in all_courses:

        # Collect my courses
        if course.instructor_id == current_user.id:
            my_courses.append(course)
            continue  # don't recommend own course

        # SEARCH MODE (if search is used)
        if search_query:
            if search_query.lower() in (course.title or "").lower():
                matched_courses.append(course)
            continue

        # RECOMMENDATION MODE
        if skills_list:
            course_tags = (course.tags or "").lower()
            for skill in skills_list:
                if skill in course_tags:
                    matched_courses.append(course)
                    break

    # Enrolled courses
    enrollments = Enrollment.query.filter_by(
        student_id=current_user.id
    ).all()

    for enrollment in enrollments:
        course = Course.query.get(enrollment.course_id)
        if course:
            enrolled_courses.append(course)

    return render_template(
        "dashboard.html",
        user=current_user,
        courses=matched_courses,
        my_courses=my_courses,
        enrolled_courses=enrolled_courses
    )


@dashboard_bp.route("/transactions")
@login_required
def transactions():

    user_transactions = CreditTransaction.query.filter_by(
        user_id=current_user.id
    ).order_by(CreditTransaction.timestamp.desc()).all()

    return render_template(
        "transactions.html",
        transactions=user_transactions
    )


@dashboard_bp.route("/leaderboard")
@login_required
def leaderboard():

    users = User.query.order_by(User.credits.desc()).limit(10).all()

    return render_template(
        "leaderboard.html",
        users=users
    )