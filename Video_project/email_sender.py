from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from db import get_db

SENDGRID_API_KEY = "nuh-uh"
FROM_EMAIL = "mauriciomendoza@dusty.tamiu.edu"


def initial_email_to_employee(user_id):
    db = get_db()
    latest = db.execute(
        """
        SELECT
            fr.id,
            fr.camera_location,
            fr.start_time,
            fr.end_time,
            fr.reason,
            u.email AS user_email,
            u.department,
            u.first_name,
            u.last_name
        FROM footage_requests fr
        JOIN users u ON fr.requestor_id = u.id
        WHERE fr.requestor_id = ?
        ORDER BY fr.submitted_at DESC
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()

    if not latest:
        return None

    user_email = latest["user_email"]
    department_name = latest["department"]
    camera_location = latest["camera_location"]
    start_time = latest["start_time"]
    end_time = latest["end_time"]
    reason = latest["reason"]

    director_email = None
    if department_name:
        director_row = db.execute(
            "SELECT email FROM users WHERE role = 'director' AND department = ? LIMIT 1",
            (department_name,),
        ).fetchone()
        director_email = director_row["email"] if director_row else None

    nice_department = ""
    if department_name:
        nice_department = department_name.replace("_", " ").title()

    users_body = f"<p>Your request was submitted successfully.</p>"
    users_body += f"<ul><li>Camera location: {camera_location}</li>"
    users_body += f"<li>Start: {start_time}</li>"
    users_body += f"<li>End: {end_time}</li>"
    users_body += f"<li>Reason: {reason}</li>"
    users_body += f"<li>Department: {nice_department or 'N/A'}</li></ul>"

    director_body = f"<p>A new footage request was submitted by {latest['first_name']} {latest['last_name']}.</p>"
    director_body += f"<ul><li>Camera location: {camera_location}</li>"
    director_body += f"<li>Start: {start_time}</li>"
    director_body += f"<li>End: {end_time}</li>"
    director_body += f"<li>Reason: {reason}</li>"
    director_body += f"<li>Department: {nice_department or 'N/A'}</li></ul>"
    director_body += '<p><a href="http://127.0.0.1:5000/login">Click here to login and view requests</a></p>'

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)

        employee_msg = Mail(
            from_email=FROM_EMAIL,
            to_emails=user_email,
            subject="Footage request received",
            html_content=users_body,
        )
        sg.send(employee_msg)

        if director_email:
            director_msg = Mail(
                from_email=FROM_EMAIL,
                to_emails=director_email,
                subject="New Footage Request Pending Approval",
                html_content=director_body,
            )
            sg.send(director_msg)

    except Exception as e:
        print("Email error:", e)
        return False

    return True


def send_update_email(request_id):
    db = get_db()
    req = db.execute(
        """
        SELECT
            fr.id,
            fr.camera_location,
            fr.start_time,
            fr.end_time,
            fr.reason,
            fr.status,
            u.email AS user_email,
            u.department,
            u.first_name,
            u.last_name
        FROM footage_requests fr
        JOIN users u ON fr.requestor_id = u.id
        WHERE fr.id = ?
        """,
        (request_id,),
    ).fetchone()

    if not req:
        return None

    user_email = req["user_email"]
    department_name = req["department"]
    camera_location = req["camera_location"]
    start_time = req["start_time"]
    end_time = req["end_time"]
    reason = req["reason"]
    status = req["status"]

    nice_department = ""
    if department_name:
        nice_department = department_name.replace("_", " ").title()

    message_body = f"<p>Your request #{request_id} has been updated to <strong>{status.upper()}</strong>:</p>"
    message_body += f"<ul><li>Camera location: {camera_location}</li>"
    message_body += f"<li>Start: {start_time}</li>"
    message_body += f"<li>End: {end_time}</li>"
    message_body += f"<li>Reason: {reason}</li>"
    message_body += f"<li>Department: {nice_department or 'N/A'}</li></ul>"

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=user_email,
        subject=f"Footage Request #{request_id} Update",
        html_content=message_body,
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return True
    except Exception as e:
        print("Email error:", e)
        return False


def send_tech_email(request_id):
    db = get_db()
    req = db.execute(
        """
        SELECT
            fr.id,
            fr.camera_location,
            fr.start_time,
            fr.end_time,
            fr.reason,
            u.email AS user_email,
            u.department,
            u.first_name,
            u.last_name
        FROM footage_requests fr
        JOIN users u ON fr.requestor_id = u.id
        WHERE fr.id = ?
        """,
        (request_id,),
    ).fetchone()

    if not req:
        return None

    camera_location = req["camera_location"]
    start_time = req["start_time"]
    end_time = req["end_time"]
    reason = req["reason"]

    tech = db.execute(
        "SELECT email FROM users WHERE role = 'tech' AND department = ? LIMIT 1",
        (req["department"],)
    ).fetchone()

    if not tech:
        print(f"No tech found for department: {req['department']}")
        return False

    message_body = f"<p>Request #{request_id} has been approved and requires your attention:</p>"
    message_body += f"<ul><li>Camera location: {camera_location}</li>"
    message_body += f"<li>Start: {start_time}</li>"
    message_body += f"<li>End: {end_time}</li>"
    message_body += f"<li>Reason: {reason}</li></ul>"
    message_body += '<p><a href="http://127.0.0.1:5000/login">Click here to login and view requests</a></p>'

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=tech["email"],
        subject=f"Footage Request #{request_id} Approved - Action Required",
        html_content=message_body,
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return True
    except Exception as e:
        print("Email error:", e)
        return False


def send_final_email(request_id):
    db = get_db()
    req = db.execute(
        """
        SELECT
            fr.id,
            fr.camera_location,
            fr.start_time,
            fr.end_time,
            fr.reason,
            u.email AS user_email,
            u.department,
            u.first_name,
            u.last_name
        FROM footage_requests fr
        JOIN users u ON fr.requestor_id = u.id
        WHERE fr.id = ?
        """,
        (request_id,),
    ).fetchone()

    if not req:
        return None

    user_email = req["user_email"]
    department_name = req["department"]
    camera_location = req["camera_location"]
    start_time = req["start_time"]
    end_time = req["end_time"]
    reason = req["reason"]

    nice_department = ""
    if department_name:
        nice_department = department_name.replace("_", " ").title()

    message_body = f"<p>Your request #{request_id} has been completed. The footage is now available for review.</p>"
    message_body += f"<ul><li>Camera location: {camera_location}</li>"
    message_body += f"<li>Start: {start_time}</li>"
    message_body += f"<li>End: {end_time}</li>"
    message_body += f"<li>Reason: {reason}</li>"
    message_body += f"<li>Department: {nice_department or 'N/A'}</li></ul>"
    message_body += '<p>The Network Technician has added the location of the network share folder and the password to access the folder contents. To find the folder, open File Explorer, go to "Network" on the left-hand side, and follow the same path provided.</p>'
    message_body += '<p><a href="http://127.0.0.1:5000/login">Click here to login and view the completed request</a></p>'

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=user_email,
        subject=f"Footage Request #{request_id} Completed",
        html_content=message_body,
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return True
    except Exception as e:
        print("Email error:", e)
        return False