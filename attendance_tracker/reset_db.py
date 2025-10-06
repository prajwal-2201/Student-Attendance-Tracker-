# reset_db.py
from app import app, db
import models   # ✅ make sure models are imported so all tables are registered
from sqlalchemy import text

with app.app_context():
    # Temporarily disable foreign key checks (needed for MySQL)
    db.session.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
    
    # Drop and recreate all tables
    db.drop_all()
    db.create_all()
    
    # Re-enable foreign key checks
    db.session.execute(text("SET FOREIGN_KEY_CHECKS=1;"))
    db.session.commit()
    
    # Sanity check: print all created tables
    print("✅ Database reset complete. Tables created:")
    for table in db.metadata.tables.keys():
        print(" -", table)
