from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import bcrypt
import pandas as pd
from werkzeug.utils import secure_filename
import os
from datetime import date as dt_date

import config
from models import db, Admin, Student, Professor, Subject, Routine, Attendance

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


# -------------------- LOGIN MANAGER --------------------
@login_manager.user_loader
def load_user(user_id):
    """Flask-Login needs this: user_id looks like 'admin-1' or 'student-22'"""
    if user_id.startswith("admin-"):
        return Admin.query.get(int(user_id.split("-")[1]))
    elif user_id.startswith("student-"):
        return Student.query.get(user_id.split("-")[1])
    elif user_id.startswith("prof-"):
        return Professor.query.get(int(user_id.split("-")[1]))
    return None


# -------------------- HOME --------------------
@app.route("/")
def home():
    if current_user.is_authenticated:
        if isinstance(current_user, Admin):
            return redirect(url_for("dashboard_admin"))
        elif isinstance(current_user, Student):
            return redirect(url_for("dashboard_student"))
        elif isinstance(current_user, Professor):
            return redirect(url_for("dashboard_prof"))
    return redirect(url_for("login"))


# -------------------- LOGIN/LOGOUT --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        username = request.form.get("username")
        password = request.form.get("password")

        if role == "admin":
            user = Admin.query.filter_by(username=username).first()
        elif role == "student":
            user = Student.query.filter_by(enrol_no=username).first()
        else:  # professor
            user = Professor.query.filter_by(username=username).first()

        if user and bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
            login_user(user)
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# -------------------- DASHBOARDS --------------------
@app.route("/admin/dashboard")
@login_required
def dashboard_admin():
    return render_template("dashboard_admin.html")


@app.route("/prof/dashboard")
@login_required
def dashboard_prof():
    if not isinstance(current_user, Professor):
        flash("Access denied", "danger")
        return redirect(url_for("home"))

    routines = (
        db.session.query(Routine, Subject)
        .join(Subject, Routine.sub_id == Subject.sub_id)
        .filter(Routine.prof_id == current_user.prof_id)
        .order_by(Routine.day, Routine.timing)
        .all()
    )

    return render_template("dashboard_prof.html", routines=routines)


# -------------------- BULK UPLOAD --------------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload limit

@app.route("/admin/upload/<datatype>", methods=["GET", "POST"])
@login_required
def admin_upload(datatype):
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            flash("No file uploaded", "danger")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        df = pd.read_csv(filepath)

        if datatype == "students":
            for _, row in df.iterrows():
                pw_hash = bcrypt.hashpw(row["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                s = Student(
                    enrol_no=row["enrol_no"],
                    class_roll=row["class_roll"],
                    name=row["name"],
                    password_hash=pw_hash,
                    email=row["email"],
                    parent_email=row.get("parent_email"),
                    year=row["year"],
                    section=row["section"]
                )
                db.session.add(s)

        elif datatype == "professors":
            for _, row in df.iterrows():
                pw_hash = bcrypt.hashpw(row["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                p = Professor(
                    username=row["username"],
                    name=row["name"],
                    email=row["email"],
                    password_hash=pw_hash
                )
                db.session.add(p)

        elif datatype == "subjects":
            for _, row in df.iterrows():
                sub = Subject(
                    sub_code=row["sub_code"],
                    sub_name=row["sub_name"],
                    year=row["year"]
                )
                db.session.add(sub)

        elif datatype == "routine":
            for _, row in df.iterrows():
                subj = Subject.query.filter_by(sub_code=row["sub_code"]).first()
                prof = Professor.query.filter_by(username=row["prof_username"]).first()
                r = Routine(
                    day=row["day"],
                    timing=row["timing"],
                    year=row["year"],
                    section=row["section"],
                    sub_id=subj.sub_id if subj else None,
                    prof_id=prof.prof_id if prof else None
                )
                db.session.add(r)

        db.session.commit()
        flash(f"{datatype.capitalize()} uploaded successfully!", "success")
        return redirect(url_for("dashboard_admin"))

    return render_template("admin_upload.html", datatype=datatype)


# -------------------- STUDENTS CRUD --------------------
@app.route("/admin/students")
@login_required
def admin_students():
    students = Student.query.all()
    return render_template("admin_students.html", students=students)


@app.route("/admin/students/add", methods=["GET", "POST"])
@login_required
def admin_add_student():
    if request.method == "POST":
        enrol_no = request.form["enrol_no"]
        class_roll = request.form["class_roll"]
        name = request.form["name"]
        password = request.form["password"]
        email = request.form["email"]
        year = request.form["year"]
        section = request.form["section"]

        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        new_student = Student(
            enrol_no=enrol_no,
            class_roll=class_roll,
            name=name,
            password_hash=pw_hash,
            email=email,
            year=year,
            section=section
        )
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for("admin_students"))
    return render_template("admin_add_student.html")


@app.route("/admin/students/delete/<enrol_no>", methods=["POST"])
@login_required
def admin_delete_student(enrol_no):
    student = Student.query.filter_by(enrol_no=enrol_no).first()
    if student:
        db.session.delete(student)
        db.session.commit()
        flash("Student deleted successfully", "success")
    else:
        flash("Student not found", "danger")
    return redirect(url_for("admin_students"))


# -------------------- STUDENT DASHBOARD --------------------
@app.route("/student/dashboard")
@login_required
def dashboard_student():
    if not isinstance(current_user, Student):
        flash("Access denied", "danger")
        return redirect(url_for("home"))

    # Fetch timetable for this student's year & section
    routines = (
        db.session.query(Routine, Subject, Professor)
        .join(Subject, Routine.sub_id == Subject.sub_id)
        .join(Professor, Routine.prof_id == Professor.prof_id)
        .filter(Routine.year == current_user.year, Routine.section == current_user.section)
        .order_by(Routine.day, Routine.timing)
        .all()
    )

    # Fetch attendance for summary
    records = (
        db.session.query(Attendance, Subject)
        .join(Subject, Attendance.sub_id == Subject.sub_id)
        .filter(Attendance.enrol_no == current_user.enrol_no)
        .all()
    )

    # --- Attendance Summary Calculation ---
    summary = {}
    for att, sub in records:
        if sub.sub_name not in summary:
            summary[sub.sub_name] = {"total": 0, "attended": 0}
        summary[sub.sub_name]["total"] += 1
        if att.status.lower() == "present":
            summary[sub.sub_name]["attended"] += 1

    # Convert to list with percentage
    summary_list = []
    for sub_name, data in summary.items():
        total = data["total"]
        attended = data["attended"]
        percent = round((attended / total) * 100, 2) if total > 0 else 0
        summary_list.append({
            "subject": sub_name,
            "total": total,
            "attended": attended,
            "percent": percent
        })

    return render_template("dashboard_student.html", routines=routines, summary=summary_list)


# -------------------- STUDENT DETAILED ATTENDANCE --------------------
@app.route("/student/attendance")
@login_required
def student_attendance():
    if not isinstance(current_user, Student):
        flash("Access denied", "danger")
        return redirect(url_for("home"))

    # Detailed records only
    records = (
        db.session.query(Attendance, Subject)
        .join(Subject, Attendance.sub_id == Subject.sub_id)
        .filter(Attendance.enrol_no == current_user.enrol_no)
        .order_by(Attendance.class_date.desc())
        .all()
    )

    return render_template("student_attendance.html", records=records)


# -------------------- PROFESSORS CRUD --------------------
@app.route("/admin/professors")
@login_required
def admin_professors():
    professors = Professor.query.all()
    return render_template("admin_professors.html", professors=professors)


@app.route("/admin/professors/add", methods=["GET", "POST"])
@login_required
def admin_add_professor():
    if request.method == "POST":
        username = request.form["username"]
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        new_prof = Professor(username=username, name=name, email=email, password_hash=pw_hash)
        db.session.add(new_prof)
        db.session.commit()
        flash("Professor added successfully", "success")
        return redirect(url_for("admin_professors"))
    return render_template("admin_add_professor.html")


@app.route("/admin/professors/delete/<int:prof_id>", methods=["POST"])
@login_required
def admin_delete_professor(prof_id):
    prof = Professor.query.get(prof_id)
    if prof:
        db.session.delete(prof)
        db.session.commit()
        flash("Professor deleted successfully", "success")
    else:
        flash("Professor not found", "danger")
    return redirect(url_for("admin_professors"))


@app.route("/prof/routine")
@login_required
def prof_routine():
    routines = Routine.query.filter_by(prof_id=current_user.prof_id).all()
    return render_template("prof_routine.html", routines=routines)


# ✅ FIXED: Only one version of prof_take_attendance
@app.route("/prof/attendance/<int:routine_id>", methods=["GET", "POST"])
@login_required
def prof_take_attendance(routine_id):
    routine = Routine.query.get(routine_id)
    if not routine or routine.prof_id != current_user.prof_id:
        flash("Invalid routine", "danger")
        return redirect(url_for("prof_routine"))

    students = Student.query.filter_by(year=routine.year, section=routine.section).all()

    if request.method == "POST":
        date_val = request.form.get("date")
        if not date_val or date_val.strip() == "":
            date_val = dt_date.today().strftime("%Y-%m-%d")

        for student in students:
            status = request.form.get(f"status_{student.enrol_no}")
            new_att = Attendance(
                enrol_no=student.enrol_no,
                sub_id=routine.sub_id,
                class_date=date_val,
                status=status,
                routine_id=routine.routine_id,
                prof_id=current_user.prof_id
            )
            db.session.add(new_att)
        db.session.commit()
        flash("Attendance saved successfully", "success")
        return redirect(url_for("prof_routine"))

    return render_template(
        "prof_take_attendance.html",
        routine=routine,
        students=students,
        current_date=dt_date.today().strftime("%Y-%m-%d")
    )


@app.route("/prof/attendance/records")
@login_required
def prof_attendance_records():
    records = (
        db.session.query(Attendance, Student, Subject)
        .join(Student, Attendance.enrol_no == Student.enrol_no)
        .join(Subject, Attendance.sub_id == Subject.sub_id)
        .filter(Attendance.prof_id == current_user.prof_id)
        .all()
    )
    return render_template("prof_attendance_records.html", records=records)


# -------------------- SUBJECTS CRUD --------------------
@app.route("/admin/subjects")
@login_required
def admin_subjects():
    subjects = Subject.query.all()
    return render_template("admin_subjects.html", subjects=subjects)


@app.route("/admin/subjects/add", methods=["GET", "POST"])
@login_required
def admin_add_subject():
    if request.method == "POST":
        sub_code = request.form["sub_code"]
        sub_name = request.form["sub_name"]
        year = request.form["year"]

        new_sub = Subject(sub_code=sub_code, sub_name=sub_name, year=year)
        db.session.add(new_sub)
        db.session.commit()
        flash("Subject added successfully", "success")
        return redirect(url_for("admin_subjects"))
    return render_template("admin_add_subject.html")


@app.route("/admin/subjects/delete/<int:sub_id>", methods=["POST"])
@login_required
def admin_delete_subject(sub_id):
    subj = Subject.query.get(sub_id)
    if subj:
        db.session.delete(subj)
        db.session.commit()
        flash("Subject deleted successfully", "success")
    else:
        flash("Subject not found", "danger")
    return redirect(url_for("admin_subjects"))


# -------------------- ROUTINES CRUD --------------------
@app.route("/admin/routines")
@login_required
def admin_routines():
    routines = Routine.query.all()
    return render_template("admin_routines.html", routines=routines)


@app.route("/admin/routines/add", methods=["GET", "POST"])
@login_required
def admin_add_routine():
    if request.method == "POST":
        day = request.form["day"]
        timing = request.form["timing"]
        year = request.form["year"]
        section = request.form["section"]
        sub_code = request.form["sub_code"]
        prof_username = request.form["prof_username"]

        subj = Subject.query.filter_by(sub_code=sub_code).first()
        prof = Professor.query.filter_by(username=prof_username).first()

        if not subj or not prof:
            flash("Invalid Subject Code or Professor Username", "danger")
            return redirect(url_for("admin_add_routine"))

        new_routine = Routine(
            day=day, timing=timing, year=year, section=section,
            sub_id=subj.sub_id, prof_id=prof.prof_id
        )
        db.session.add(new_routine)
        db.session.commit()
        flash("Routine added successfully", "success")
        return redirect(url_for("admin_routines"))
    return render_template("admin_add_routine.html")


@app.route("/admin/routine/delete/<int:routine_id>", methods=["POST"])
@login_required
def admin_delete_routine(routine_id):
    routine = Routine.query.get(routine_id)
    if routine:
        db.session.delete(routine)
        db.session.commit()
        flash("Routine deleted successfully", "success")
    else:
        flash("Routine not found", "danger")
    return redirect(url_for("admin_routines"))


from sqlalchemy import text  # ✅ add this import at the top of app.py


@app.route("/admin/alerts")
@login_required
def admin_alerts():
    if not isinstance(current_user, Admin):
        flash("Access denied", "danger")
        return redirect(url_for("home"))

    # ✅ Wrap raw SQL query inside text()
    sql = text("""
        SELECT a.alert_id, a.alert_type, a.percent, a.class_date,
               s.name AS student_name, s.enrol_no,
               sub.sub_name
        FROM attendance_alerts a
        JOIN students s ON a.enrol_no = s.enrol_no
        JOIN subjects sub ON a.sub_id = sub.sub_id
        ORDER BY a.created_at DESC
    """)

    alerts = db.session.execute(sql).fetchall()

    return render_template("admin_alerts.html", alerts=alerts)



# -------------------- MAIN --------------------
if __name__ == "__main__":
    app.run(debug=True)
