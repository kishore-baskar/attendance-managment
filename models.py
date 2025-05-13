from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'student' or 'teacher'
    subject = db.Column(db.String(100))  # Only for teachers
    leaves = db.relationship('Leave', backref='student', lazy=True, foreign_keys='Leave.student_id')

class Leave(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(10), default='Pending')  # Pending, Approved, Rejected
    teacher_comment = db.Column(db.String(200))
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # The teacher selected for this leave
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='assigned_leaves', lazy=True)
    category = db.Column(db.String(50), nullable=False)  # Leave category
    date_applied = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # When the leave was applied 