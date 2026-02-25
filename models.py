from extensions import db
from flask_login import UserMixin
from datetime import datetime


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    full_name = db.Column(db.String(150))
    college = db.Column(db.String(150))
    degree = db.Column(db.String(150))
    bio = db.Column(db.Text)

    profile_pic = db.Column(db.String(300))

    skills_teach = db.Column(db.String(300))
    skills_learn = db.Column(db.String(300))

    credits = db.Column(db.Integer, default=0)
    bought_credits = db.Column(db.Integer, default=0)
    karma = db.Column(db.Integer, default=0)

    is_profile_complete = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))
    description = db.Column(db.Text)

    tags = db.Column(db.String(300))  # IMPORTANT for feed matching

    duration = db.Column(db.Integer)  # in minutes
    credits_required = db.Column(db.Integer)

    video_path = db.Column(db.String(300))
    document_path = db.Column(db.String(300))

    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    thumbnail_path = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviews = db.relationship('Review', backref='course', lazy=True)

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))

    completed = db.Column(db.Boolean, default=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)


class CreditTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Integer)
    type = db.Column(db.String(50))  # earn / spend / purchase
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))

    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class LiveSessionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    proposed_credits = db.Column(db.Integer)
    status = db.Column(db.String(50), default="pending")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))

    certificate_id = db.Column(db.String(100), unique=True)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)

class OTPVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150))
    otp = db.Column(db.String(10))
    password = db.Column(db.String(200))   # ADD THIS
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PlatformWallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_credits = db.Column(db.Integer, default=0)