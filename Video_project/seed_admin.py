from werkzeug.security import generate_password_hash
from app import create_app
from db import get_db

app = create_app()

with app.app_context():
    db = get_db()

    email = "admin@laredo.local"
    pw_hash = generate_password_hash("ChangeMe123!", method="pbkdf2:sha256")
    db.execute("""
        INSERT OR IGNORE INTO users (employee_id, first_name, last_name, email, password_hash, role, department, division, job_title)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ("CoLA001", "System", "Admin", email, pw_hash, "admin", "IT", "IT", "System Administrator"))

    db.commit()
    user = db.execute("""
        SELECT id FROM users WHERE email = ?
    """, (email,)).fetchone()
    if(user):
        print("Admin seeded (if not already present).")
    else: 
        print("seed failed")