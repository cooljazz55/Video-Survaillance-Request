from werkzeug.security import generate_password_hash
from app import create_app
from db import get_db

app = create_app()

with app.app_context():
    db = get_db()

    email = "requestor@laredo.local"
    pw_hash = generate_password_hash("Requestor123!", method="pbkdf2:sha256")

    db.execute("""
        INSERT OR IGNORE INTO users (first_name, last_name, email, password_hash, role, department)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("Test", "Requestor", email, pw_hash, "requestor", "Public Safety"))

    db.commit()
    print("Requestor seeded (if not already present).")