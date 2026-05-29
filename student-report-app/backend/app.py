import csv
import io
import os
import sys

# Ensure backend directory is in sys.path for Vercel serverless imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from functools import wraps
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from models import Student, Admin, db
from email_service import send_report_email, verify_credentials

# ─────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "acatier-secure-secret-key-2026")
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

basedir = os.path.abspath(os.path.dirname(__file__))
is_vercel = os.environ.get("VERCEL") == "1"

if is_vercel:
    db_url = os.environ.get("DATABASE_URL", "sqlite:////tmp/students.db")
else:
    db_url = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(basedir, "instance", "students.db"))

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    if not is_vercel and not db_url.startswith("sqlite:////tmp/"):
        os.makedirs(os.path.join(basedir, "instance"), exist_ok=True)
    db.drop_all()
    db.create_all()
    
    # Auto-seed default administrator if none exists
    if not Admin.query.filter_by(username="admin").first():
        default_admin = Admin(username="admin", email="admin@acatier.local")
        default_admin.set_password("admin123")
        db.session.add(default_admin)
        db.session.commit()
        print("Seeded default admin: admin / admin123")

    # Seed the requested subhi admin credentials
    if not Admin.query.filter_by(username="subhi").first():
        subhi_admin = Admin(username="subhi", email="subhi@acatier.local")
        subhi_admin.set_password("selva")
        db.session.add(subhi_admin)
        db.session.commit()
        print("Seeded subhi admin: subhi / selva")


# ─────────────────────────────────────────────
# Helper — recalculate all ranks
# ─────────────────────────────────────────────
def _recalculate_ranks():
    students = Student.query.order_by(Student.total.desc()).all()
    for rank, student in enumerate(students, start=1):
        student.rank = rank
    db.session.commit()


# ─────────────────────────────────────────────
# Decorator — Require Timed Signed Token
# ─────────────────────────────────────────────
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Token is missing", "code": "UNAUTHORIZED"}), 401
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Invalid Authorization header format", "code": "UNAUTHORIZED"}), 401
        
        token = parts[1]
        try:
            # Token valid for 2 hours (7200 seconds)
            data = serializer.loads(token, max_age=7200)
            current_admin = Admin.query.get(data["admin_id"])
            if not current_admin:
                return jsonify({"error": "Admin user not found", "code": "UNAUTHORIZED"}), 401
        except SignatureExpired:
            return jsonify({"error": "Token has expired", "code": "TOKEN_EXPIRED"}), 401
        except BadSignature:
            return jsonify({"error": "Invalid token", "code": "UNAUTHORIZED"}), 401
        except Exception:
            return jsonify({"error": "Authentication error", "code": "UNAUTHORIZED"}), 401
        
        return f(current_admin, *args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
# Auth Routes
# ─────────────────────────────────────────────

# POST /api/auth/login  — authenticate administrator
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    admin = Admin.query.filter_by(username=username).first()
    if not admin or not admin.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401

    # Generate timed secure token
    token = serializer.dumps({"admin_id": admin.id})
    return jsonify({
        "success": True,
        "token": token,
        "admin": admin.to_dict()
    })


# GET /api/auth/me  — retrieve current logged in administrator
@app.route("/api/auth/me", methods=["GET"])
@token_required
def get_current_user(current_admin):
    return jsonify({
        "success": True,
        "admin": current_admin.to_dict()
    })


# POST /api/auth/change-password  — change administrator password
@app.route("/api/auth/change-password", methods=["POST"])
@token_required
def change_password(current_admin):
    data = request.get_json() or {}
    old_password = data.get("old_password", "").strip()
    new_password = data.get("new_password", "").strip()

    if not old_password or not new_password:
        return jsonify({"error": "Old and new passwords are required"}), 400

    if not current_admin.check_password(old_password):
        return jsonify({"error": "Incorrect current password"}), 400

    current_admin.set_password(new_password)
    db.session.commit()
    return jsonify({"success": True, "message": "Password changed successfully"})


# ─────────────────────────────────────────────
# Student Routes
# ─────────────────────────────────────────────

# POST /api/students  — add a new student (Protected)
@app.route("/api/students", methods=["POST"])
@token_required
def add_student(current_admin):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    name         = data.get("name", "").strip()
    parent_email = data.get("parent_email", "").strip()
    marks        = data.get("marks", [])
    grade        = str(data.get("grade", "10")).strip()
    group        = data.get("group")
    if group:
        group = str(group).strip()

    if not name or not parent_email or not marks:
        return jsonify({"error": "name, parent_email and marks are required"}), 400

    try:
        marks = [int(m) for m in marks]
    except (ValueError, TypeError):
        return jsonify({"error": "marks must be integers"}), 400

    total   = sum(marks)
    average = total / len(marks)

    student = Student(name=name, parent_email=parent_email,
                      total=total, average=average,
                      grade=grade, group=group)
    student.marks = marks

    db.session.add(student)
    db.session.commit()
    _recalculate_ranks()
    db.session.refresh(student)

    return jsonify(student.to_dict()), 201


# GET /api/students  — list all students (ranked - Public)
@app.route("/api/students", methods=["GET"])
def get_students():
    students = Student.query.order_by(Student.rank).all()
    return jsonify([s.to_dict() for s in students])


# DELETE /api/students/<id>  — remove a student (Protected)
@app.route("/api/students/<int:student_id>", methods=["DELETE"])
@token_required
def delete_student(current_admin, student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    _recalculate_ranks()
    return jsonify({"message": f"Student '{student.name}' deleted"})


# GET /api/summary  — grade distribution (Public)
@app.route("/api/summary", methods=["GET"])
def get_summary():
    students = Student.query.all()
    ranges = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "Below 60": 0}

    for s in students:
        avg = s.average
        if avg >= 90:
            ranges["90-100"] += 1
        elif avg >= 80:
            ranges["80-89"] += 1
        elif avg >= 70:
            ranges["70-79"] += 1
        elif avg >= 60:
            ranges["60-69"] += 1
        else:
            ranges["Below 60"] += 1

    total_students = len(students)
    top_student = (
        Student.query.order_by(Student.total.desc()).first()
    )

    return jsonify({
        "total_students": total_students,
        "grade_distribution": ranges,
        "top_student": top_student.to_dict() if top_student else None,
        "class_average": (
            round(sum(s.average for s in students) / total_students, 2)
            if total_students else 0
        ),
    })


# POST /api/verify-credentials  — test Gmail login (no email sent - Protected)
@app.route("/api/verify-credentials", methods=["POST"])
@token_required
def verify_creds(current_admin):
    data            = request.get_json()
    sender_email    = (data or {}).get("sender_email", "").strip()
    sender_password = (data or {}).get("sender_password", "").strip()

    if not sender_email or not sender_password:
        return jsonify({"error": "sender_email and sender_password are required"}), 400

    result = verify_credentials(sender_email, sender_password)
    return jsonify(result), 200 if result["success"] else 401


# POST /api/send-emails  — send emails to ALL parents (Protected)
@app.route("/api/send-emails", methods=["POST"])
@token_required
def send_emails(current_admin):
    data = request.get_json()
    sender_email    = (data or {}).get("sender_email", "").strip()
    sender_password = (data or {}).get("sender_password", "").strip()

    if not sender_email or not sender_password:
        return jsonify({"error": "sender_email and sender_password are required"}), 400

    students = Student.query.order_by(Student.rank).all()
    if not students:
        return jsonify({"error": "No students found in the database"}), 400

    results = []
    for s in students:
        result = send_report_email(s.to_dict(), sender_email, sender_password)
        if result["success"]:
            s.email_sent = True
        results.append({"student": s.name, **result})

    db.session.commit()
    return jsonify({"results": results})


# POST /api/send-email/<id>  — send email to ONE parent (Protected)
@app.route("/api/send-email/<int:student_id>", methods=["POST"])
@token_required
def send_single_email(current_admin, student_id):
    student = Student.query.get_or_404(student_id)
    data = request.get_json()
    sender_email    = (data or {}).get("sender_email", "").strip()
    sender_password = (data or {}).get("sender_password", "").strip()

    if not sender_email or not sender_password:
        return jsonify({"error": "sender_email and sender_password are required"}), 400

    result = send_report_email(student.to_dict(), sender_email, sender_password)
    if result["success"]:
        student.email_sent = True
        db.session.commit()

    return jsonify({"student": student.name, **result})


# GET /api/export-csv  — download CSV (Protected via query token)
@app.route("/api/export-csv", methods=["GET"])
def export_csv():
    token = request.args.get("token")
    if not token:
        return jsonify({"error": "Token is missing", "code": "UNAUTHORIZED"}), 401
    try:
        data = serializer.loads(token, max_age=7200)
        current_admin = Admin.query.get(data["admin_id"])
        if not current_admin:
            return jsonify({"error": "Admin user not found", "code": "UNAUTHORIZED"}), 401
    except SignatureExpired:
        return jsonify({"error": "Token has expired", "code": "TOKEN_EXPIRED"}), 401
    except Exception:
        return jsonify({"error": "Invalid or expired token", "code": "UNAUTHORIZED"}), 401

    students = Student.query.order_by(Student.rank).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Rank", "Name", "Class", "Group", "Marks", "Total", "Average", "Parent Email", "Email Sent"])

    for s in students:
        writer.writerow([
            s.rank,
            s.name,
            s.grade,
            s.group or "—",
            " | ".join(str(m) for m in s.marks),
            s.total,
            f"{s.average:.2f}",
            s.parent_email,
            "Yes" if s.email_sent else "No",
        ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.read().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="student_results.csv",
    )


# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
