from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# ----- Admin -----
class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    admin_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def get_id(self):
        return f"admin-{self.admin_id}"


# ----- Student -----
class Student(UserMixin, db.Model):
    __tablename__ = 'students'
    enrol_no = db.Column(db.String(20), primary_key=True)
    class_roll = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(150))
    parent_email = db.Column(db.String(150))
    year = db.Column(db.Integer, nullable=False)
    section = db.Column(db.String(10), nullable=False)

    def get_id(self):
        return f"student-{self.enrol_no}"


# ----- Professor -----
class Professor(UserMixin, db.Model):
    __tablename__ = 'professors'
    prof_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(150))

    def get_id(self):
        return f"prof-{self.prof_id}"


# ----- Subject -----
class Subject(db.Model):
    __tablename__ = 'subjects'
    sub_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sub_code = db.Column(db.String(20), unique=True, nullable=False)   # 🔑 consistent
    sub_name = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer, nullable=False)


# ----- Routine -----
class Routine(db.Model):
    __tablename__ = 'routine'
    routine_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    day = db.Column(db.Enum('Mon','Tue','Wed','Thu','Fri','Sat','Sun'), nullable=False)
    timing = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    section = db.Column(db.String(10), nullable=False)
    sub_id = db.Column(db.Integer, db.ForeignKey('subjects.sub_id'))
    prof_id = db.Column(db.Integer, db.ForeignKey('professors.prof_id'))
    subject = db.relationship("Subject", backref="routines")
    professor = db.relationship("Professor", backref="routines")


# ----- Attendance -----
class Attendance(db.Model):
    __tablename__ = 'attendance'
    attendance_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    enrol_no = db.Column(db.String(20), db.ForeignKey('students.enrol_no'), nullable=False)
    class_date = db.Column(db.Date, nullable=False)
    routine_id = db.Column(db.Integer, db.ForeignKey('routine.routine_id'))
    period = db.Column(db.String(50))
    sub_id = db.Column(db.Integer, db.ForeignKey('subjects.sub_id'))
    prof_id = db.Column(db.Integer, db.ForeignKey('professors.prof_id'))
    status = db.Column(db.Enum('present','absent','leave','late'), default='present', nullable=False)
    marked_by = db.Column(db.Integer)
    remarks = db.Column(db.String(255))


# ----- Student-Subjects Association -----
student_subjects = db.Table(
    'student_subjects',
    db.Column('enrol_no', db.String(20), db.ForeignKey('students.enrol_no'), primary_key=True),
    db.Column('sub_id', db.Integer, db.ForeignKey('subjects.sub_id'), primary_key=True)
)

# ----- Professor-Subjects Association -----
professor_subjects = db.Table(
    'professor_subjects',
    db.Column('prof_id', db.Integer, db.ForeignKey('professors.prof_id'), primary_key=True),
    db.Column('sub_id', db.Integer, db.ForeignKey('subjects.sub_id'), primary_key=True)
)

# ----- Attendance Stats -----
class AttendanceStats(db.Model):
    __tablename__ = 'attendance_stats'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    enrol_no = db.Column(db.String(20), db.ForeignKey('students.enrol_no'))
    sub_id = db.Column(db.Integer, db.ForeignKey('subjects.sub_id'))
    total_classes = db.Column(db.Integer, default=0)
    attended_classes = db.Column(db.Integer, default=0)
    percentage = db.Column(db.Float, default=0.0)
