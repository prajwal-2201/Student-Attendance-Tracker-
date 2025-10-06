from app import app, db
from models import Admin
import bcrypt

with app.app_context():
    username = "Prajwal"
    password = "prajwal2204"

    # hash password
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # check if admin already exists
    existing = Admin.query.filter_by(username=username).first()
    if not existing:
        new_admin = Admin(username=username, password_hash=pw_hash)
        db.session.add(new_admin)
        db.session.commit()
        print("✅ Admin created successfully!")
    else:
        print("⚠️ Admin already exists")
