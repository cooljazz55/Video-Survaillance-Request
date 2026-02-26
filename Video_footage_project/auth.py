from functools import wraps
from flask import request, session, redirect, url_for, flash
from werkzeug.security import check_password_hash

from db import get_db

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped
def role_required(*roles):
    """
    Usage: @role_required("admin") or @role_required("director","admin")
    """
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if session.get("user_id") is None:
                return redirect(url_for("login"))
            if session.get("role") not in roles:
                flash("You do not have permission to access that page.", "error")
                log_action("ACCESS_DENIED")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorator

def authenticate(email: str, password: str):
    """
    Returns user row if credentials are valid, else None.
    """
    db = get_db()
    user = db.execute(
        "SELECT id, first_name, last_name, email, password_hash, role, is_active FROM users WHERE email = ?",
        (email.strip().lower(),),
    ).fetchone()

    if user is None:
        return None
    if user["is_active"] != 1:
        return None
    if not check_password_hash(user["password_hash"], password):
        return None

    return user

def log_action(action: str, request_id=None):
    """
    Basic audit logger (we’ll expand later). Safe even if user not logged in.
    """
    db = get_db()
    user_id = session.get("user_id")
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ua = request.headers.get("User-Agent")

    db.execute(
        "INSERT INTO audit_logs (user_id, action, request_id, ip_address, user_agent) VALUES (?, ?, ?, ?, ?)",
        (user_id, action, request_id, ip, ua),
    )
    db.commit()