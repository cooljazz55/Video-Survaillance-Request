from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from db import close_db, init_db, get_db
from auth import authenticate, login_required, role_required, log_action
from werkzeug.security import generate_password_hash


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "change-this"
    app.config["DATABASE"] = "requests.db"

    app.teardown_appcontext(close_db)

    @app.cli.command("init-db")
    def init_db_command():
        init_db()
        print("Initialized the database.")

    @app.route("/")
    def home():
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")

            user = authenticate(email, password)
            if user is None:
                log_action("LOGIN_FAILED")
                flash("Invalid email or password.", "error")
                return render_template("login.html")

            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["name"] = f"{user['first_name']} {user['last_name']}"

            log_action("LOGIN_SUCCESS")
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            if user["role"] == "director":
                return redirect(url_for("director_dashboard"))
            if user["role"] == "tech":
                return redirect(url_for("tech_dashboard"))
            if user["role"] == "requestor":
                return redirect(url_for("requestor_dashboard"))
        return render_template("login.html")
    
    @app.route("/create-account", methods=["GET", "POST"])
    def create_account():
        if request.method == "POST":
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            role = request.form.get("role", "")
            department = request.form.get("department", "")
            flash("Account created successfully!", "success")
            db = get_db()

            pw_hash = generate_password_hash(password, method="pbkdf2:sha256")

            db.execute("""
                INSERT OR IGNORE INTO users (first_name, last_name, email, password_hash, role, department)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (first_name, last_name, email, pw_hash, role, department))

            db.commit()
            return redirect(url_for("login"))
        return render_template("create_account.html")

    @app.route("/logout")
    def logout():
        log_action("LOGOUT")
        session.clear()
        return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        return render_template(
            "dashboard.html",
            name=session.get("name"),
            role=session.get("role"),
        )
    
    # ---- RBAC test routes ----
    @app.route("/admin")
    @login_required
    @role_required("admin")
    def admin_panel():
        return f"Admin panel. Hello {session.get('name')}!"

    @app.route("/director")
    @login_required
    @role_required("director", "admin")
    def director_panel():
        return f"Director panel. Hello {session.get('name')}!"

    @app.route("/tech")
    @login_required
    @role_required("tech", "admin")
    def tech_panel():
        return f"Tech panel. Hello {session.get('name')}!"

    # ---- Requestor routes ----
    @app.route("/request/new", methods=["GET", "POST"])
    @login_required
    @role_required("requestor", "admin")
    def new_request():
        if request.method == "POST":
            camera_location = request.form.get("camera_location", "").strip()
            start_time = request.form.get("start_time", "").strip()
            end_time = request.form.get("end_time", "").strip()
            reason = request.form.get("reason", "").strip()

            errors = []
            if not camera_location:
                errors.append("Camera location is required.")
            if not start_time:
                errors.append("Start time is required.")
            if not end_time:
                errors.append("End time is required.")
            if not reason:
                errors.append("Reason is required.")

            # Validate times
            try:
                start_dt = datetime.fromisoformat(start_time)
                end_dt = datetime.fromisoformat(end_time)
                if end_dt <= start_dt:
                    errors.append("End time must be after start time.")
            except Exception:
                errors.append("Invalid date/time format.")

            if errors:
                for e in errors:
                    flash(e, "error")
                return render_template("new_request.html")

            db = get_db()
            cur = db.execute(
                """
                INSERT INTO footage_requests
                    (requestor_id, camera_location, start_time, end_time, reason, status)
                VALUES (?, ?, ?, ?, ?, 'Pending')
                """,
                (session["user_id"], camera_location, start_time, end_time, reason),
            )
            db.commit()

            request_id = cur.lastrowid
            log_action("REQUEST_SUBMITTED", request_id=request_id)

            flash(f"Request #{request_id} submitted successfully.", "success")
            return redirect(url_for("requestor_dashboard"))

        return render_template("new_request.html")

    @app.route("/requests/mine")
    @login_required
    @role_required("requestor", "admin")
    def requestor_dashboard():
        db = get_db()
        rows = db.execute(
            """
            SELECT id, camera_location, start_time, end_time, status, submitted_at
            FROM footage_requests
            WHERE requestor_id = ?
            ORDER BY submitted_at DESC
            """,
            (session["user_id"],),
        ).fetchall()

        return render_template("requestor_dashboard.html", requests=rows)

    @app.route("/director/dashboard")
    @login_required
    @role_required("director", "admin")
    def director_dashboard():
        db = get_db()
        rows = db.execute(
            """
            SELECT id, requestor_id, camera_location, start_time, end_time, status, submitted_at
            FROM footage_requests
            ORDER BY submitted_at DESC
            """
        ).fetchall()
        return render_template("director_dashboard.html", requests=rows)


    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)