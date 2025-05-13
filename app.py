from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Leave
import csv
import io
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        subject = request.form.get('subject') if role == 'teacher' else None
        if User.query.filter((User.username==username)|(User.email==email)).first():
            error = 'Username or email already exists.'
        else:
            hashed_pw = generate_password_hash(password)
            user = User(username=username, email=email, password=hashed_pw, role=role, subject=subject)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter((User.username==username)|(User.email==username)).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid credentials.'
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'student':
        leaves = Leave.query.filter_by(student_id=current_user.id).all()
        teachers = list({leave.teacher for leave in leaves if leave.teacher is not None})
        teacher_id = request.args.get('teacher_id', type=int)
        selected_teacher = None
        filtered_leaves = leaves
        teacher_leave_count = 0
        approved_count = 0
        rejected_count = 0
        category_labels = []
        category_counts = []
        calendar_leaves = leaves
        approval_labels = []
        approval_counts = []
        rejection_labels = []
        rejection_counts = []
        if teacher_id:
            selected_teacher = next((t for t in teachers if t.id == teacher_id), None)
            filtered_leaves = [leave for leave in leaves if leave.teacher_id == teacher_id]
            teacher_leave_count = len(filtered_leaves)
            approved_count = sum(1 for l in filtered_leaves if l.status == 'Approved')
            rejected_leaves = [l for l in filtered_leaves if l.status == 'Rejected']
            rejected_count = len(rejected_leaves)
            from collections import Counter
            category_counter = Counter([leave.category for leave in rejected_leaves])
            category_labels = list(category_counter.keys())
            category_counts = list(category_counter.values())
            calendar_leaves = filtered_leaves
            approval_leaves = [l for l in filtered_leaves if l.status == 'Approved']
            rejection_leaves = [l for l in filtered_leaves if l.status == 'Rejected']
            approval_counter = Counter([leave.category for leave in approval_leaves])
            rejection_counter = Counter([leave.category for leave in rejection_leaves])
            approval_labels = list(approval_counter.keys())
            approval_counts = list(approval_counter.values())
            rejection_labels = list(rejection_counter.keys())
            rejection_counts = list(rejection_counter.values())
        stats = {
            'total': len(filtered_leaves),
            'approved': sum(1 for l in filtered_leaves if l.status == 'Approved'),
            'rejected': sum(1 for l in filtered_leaves if l.status == 'Rejected'),
            'pending': sum(1 for l in filtered_leaves if l.status == 'Pending'),
        }
        return render_template('dashboard_student.html', leaves=leaves, filtered_leaves=filtered_leaves, stats=stats, teachers=teachers, selected_teacher=selected_teacher, teacher_leave_count=teacher_leave_count, approved_count=approved_count, rejected_count=rejected_count, category_labels=category_labels, category_counts=category_counts, calendar_leaves=calendar_leaves, approval_labels=approval_labels, approval_counts=approval_counts, rejection_labels=rejection_labels, rejection_counts=rejection_counts)
    elif current_user.role == 'teacher':
        leaves = Leave.query.filter_by(teacher_id=current_user.id).all()
        # Get all students for the dropdown
        students = User.query.filter_by(role='student').all()
        stats = {
            'total': len(leaves),
            'approved': sum(1 for l in leaves if l.status == 'Approved'),
            'rejected': sum(1 for l in leaves if l.status == 'Rejected'),
            'pending': sum(1 for l in leaves if l.status == 'Pending'),
        }
        return render_template('dashboard_teacher.html', leaves=leaves, filtered_leaves=leaves, stats=stats, students=students, selected_student=None, student_leave_count=0, category_labels=[], category_counts=[])
    else:
        return 'Invalid role', 403

@app.route('/apply', methods=['GET', 'POST'])
@login_required
def apply():
    if current_user.role != 'student':
        return 'Unauthorized', 403
    message = error = None
    teachers = User.query.filter_by(role='teacher').all()
    if request.method == 'POST':
        date = request.form['date']
        reason = request.form['reason']
        teacher_id = request.form.get('teacher_id')
        category = request.form.get('category')
        if Leave.query.filter_by(student_id=current_user.id, date=date).first():
            error = 'You have already applied for leave on this date.'
        else:
            leave = Leave(student_id=current_user.id, date=date, reason=reason, teacher_id=teacher_id, category=category)
            db.session.add(leave)
            db.session.commit()
            message = 'Leave application submitted.'
    return render_template('apply_leave.html', message=message, error=error, teachers=teachers)

@app.route('/requests', methods=['GET', 'POST'])
@login_required
def requests_view():
    if current_user.role != 'teacher':
        return 'Unauthorized', 403
    if request.method == 'POST':
        leave_id = request.form['leave_id']
        action = request.form['action']
        comment = request.form.get('comment', '')
        leave = Leave.query.get(leave_id)
        if leave and leave.status == 'Pending' and leave.teacher_id == current_user.id:
            if action == 'approve':
                leave.status = 'Approved'
            elif action == 'reject':
                leave.status = 'Rejected'
            leave.teacher_comment = comment
            db.session.commit()
    # Student selection for analysis
    student_id = request.args.get('student_id', type=int)
    leaves = Leave.query.filter_by(teacher_id=current_user.id).all()
    # Show all students in dropdown, not just those who have requested leaves
    students = User.query.filter_by(role='student').all()
    selected_student = None
    student_leave_count = 0
    category_labels = []
    category_counts = []
    requested_labels = []
    requested_counts = []
    filtered_leaves = leaves

    if student_id:
        selected_student = next((s for s in students if s.id == student_id), None)
        if selected_student:
            student_leaves = [leave for leave in leaves if leave.student_id == student_id]
            student_leave_count = len(student_leaves)
            filtered_leaves = student_leaves
            
            # Calculate category statistics
            from collections import Counter
            category_counter = Counter([leave.category for leave in student_leaves])
            category_labels = list(category_counter.keys())
            category_counts = list(category_counter.values())
            
            # Calculate requested statistics
            requested_counter = Counter([leave.category for leave in student_leaves])
            requested_labels = list(requested_counter.keys())
            requested_counts = list(requested_counter.values())

    stats = {
        'total': len(filtered_leaves),
        'approved': sum(1 for l in filtered_leaves if l.status == 'Approved'),
        'rejected': sum(1 for l in filtered_leaves if l.status == 'Rejected'),
        'pending': sum(1 for l in filtered_leaves if l.status == 'Pending'),
    }
    return render_template('dashboard_teacher.html', 
                         leaves=leaves, 
                         filtered_leaves=filtered_leaves, 
                         stats=stats, 
                         students=students, 
                         selected_student=selected_student, 
                         student_leave_count=student_leave_count, 
                         category_labels=category_labels, 
                         category_counts=category_counts, 
                         requested_labels=requested_labels, 
                         requested_counts=requested_counts)

@app.route('/export-leaves')
@login_required
def export_leaves():
    if current_user.role == 'student':
        leaves = Leave.query.filter_by(student_id=current_user.id).all()
        filename = f'student_leaves_{current_user.username}_{datetime.now().strftime("%Y%m%d")}.csv'
    else:  # teacher
        student_id = request.args.get('student_id', type=int)
        if student_id:
            student = User.query.get(student_id)
            leaves = Leave.query.filter_by(teacher_id=current_user.id, student_id=student_id).all()
            filename = f'teacher_leaves_{student.username}_{datetime.now().strftime("%Y%m%d")}.csv'
        else:
            leaves = Leave.query.filter_by(teacher_id=current_user.id).all()
            filename = f'teacher_all_leaves_{datetime.now().strftime("%Y%m%d")}.csv'

    output = io.StringIO()
    writer = csv.writer(output)
    
    if current_user.role == 'student':
        writer.writerow(['Date', 'Category', 'Reason', 'Status', 'Teacher Comment'])
        for leave in leaves:
            writer.writerow([
                leave.date,
                leave.category,
                leave.reason,
                leave.status,
                leave.teacher_comment or '-'
            ])
    else:  # teacher
        writer.writerow(['Student', 'Date Applied', 'Leave Date', 'Category', 'Reason', 'Status', 'Teacher Comment'])
        for leave in leaves:
            writer.writerow([
                leave.student.username,
                leave.date_applied.strftime('%Y-%m-%d %H:%M') if leave.date_applied else '-',
                leave.date,
                leave.category,
                leave.reason,
                leave.status,
                leave.teacher_comment or '-'
            ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 