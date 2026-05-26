import csv
import io
import os

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from models import Student, db
from email_service import send_report_email, verify_credentials

# ─────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + os.path.join(basedir, "instance", "students.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    os.makedirs(os.path.join(basedir, "instance"), exist_ok=True)
    db.create_all()


# ─────────────────────────────────────────────
# Helper — recalculate all ranks
# ─────────────────────────────────────────────
def _recalculate_ranks():
    students = Student.query.order_by(Student.total.desc()).all()
    for rank, student in enumerate(students, start=1):
        student.rank = rank
    db.session.commit()


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

# POST /api/students  — add a new student
@app.route("/api/students", methods=["POST"])
def add_student():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    name         = data.get("name", "").strip()
    parent_email = data.get("parent_email", "").strip()
    marks        = data.get("marks", [])

    if not name or not parent_email or not marks:
        return jsonify({"error": "name, parent_email and marks are required"}), 400

    try:
        marks = [int(m) for m in marks]
    except (ValueError, TypeError):
        return jsonify({"error": "marks must be integers"}), 400

    total   = sum(marks)
    average = total / len(marks)

    student = Student(name=name, parent_email=parent_email,
                      total=total, average=average)
    student.marks = marks

    db.session.add(student)
    db.session.commit()
    _recalculate_ranks()
    db.session.refresh(student)

    return jsonify(student.to_dict()), 201


# GET /api/students  — list all students (ranked)
@app.route("/api/students", methods=["GET"])
def get_students():
    students = Student.query.order_by(Student.rank).all()
    return jsonify([s.to_dict() for s in students])


# DELETE /api/students/<id>  — remove a student
@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    _recalculate_ranks()
    return jsonify({"message": f"Student '{student.name}' deleted"})


# GET /api/summary  — grade distribution
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


# POST /api/verify-credentials  — test Gmail login (no email sent)
@app.route("/api/verify-credentials", methods=["POST"])
def verify_creds():
    data            = request.get_json()
    sender_email    = (data or {}).get("sender_email", "").strip()
    sender_password = (data or {}).get("sender_password", "").strip()

    if not sender_email or not sender_password:
        return jsonify({"error": "sender_email and sender_password are required"}), 400

    result = verify_credentials(sender_email, sender_password)
    return jsonify(result), 200 if result["success"] else 401


# POST /api/send-emails  — send emails to ALL parents

@app.route("/api/send-emails", methods=["POST"])
def send_emails():
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


# POST /api/send-email/<id>  — send email to ONE parent
@app.route("/api/send-email/<int:student_id>", methods=["POST"])
def send_single_email(student_id):
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


# GET /api/export-csv  — download CSV
@app.route("/api/export-csv", methods=["GET"])
def export_csv():
    students = Student.query.order_by(Student.rank).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Rank", "Name", "Marks", "Total", "Average", "Parent Email", "Email Sent"])

    for s in students:
        writer.writerow([
            s.rank,
            s.name,
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
