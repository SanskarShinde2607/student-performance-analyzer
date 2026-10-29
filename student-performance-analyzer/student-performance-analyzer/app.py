from pathlib import Path
import io
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, abort
from flask_wtf.csrf import CSRFProtect
from config import BASE_DIR, DATA_DIR, REPORTS_DIR, SECRET_KEY, ATTENDANCE_THRESHOLD, PASS_THRESHOLD, MAX_CONTENT_LENGTH
from services.csv_manager import (read_csv, atomic_write, STUDENT_COLUMNS, ATTENDANCE_COLUMNS, MARK_COLUMNS,
                                  validate_columns, validate_student)
from services.analytics import analytics_payload, student_overview
from services.risk_prediction import classify_students

app = Flask(__name__)
app.config.update(SECRET_KEY=SECRET_KEY, MAX_CONTENT_LENGTH=MAX_CONTENT_LENGTH)
CSRFProtect(app)
STUDENTS = DATA_DIR / "students.csv"
ATTENDANCE = DATA_DIR / "attendance.csv"
MARKS = DATA_DIR / "marks.csv"

def load_data():
    return (read_csv(STUDENTS, STUDENT_COLUMNS), read_csv(ATTENDANCE, ATTENDANCE_COLUMNS), read_csv(MARKS, MARK_COLUMNS))

def init_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for path, cols in [(STUDENTS, STUDENT_COLUMNS), (ATTENDANCE, ATTENDANCE_COLUMNS), (MARKS, MARK_COLUMNS)]:
        if not path.exists():
            pd.DataFrame(columns=cols).to_csv(path, index=False)

@app.context_processor
def inject_globals():
    return {"app_name": "Student Performance Analyzer"}

@app.route("/")
def index():
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    s, a, m = load_data()
    payload = analytics_payload(s, a, m, ATTENDANCE_THRESHOLD, PASS_THRESHOLD)
    charts = {
        "subject_labels": list(payload["subject_averages"].keys()),
        "subject_values": list(payload["subject_averages"].values()),
        "attendance_labels": list(payload["attendance_buckets"].keys()),
        "attendance_values": list(payload["attendance_buckets"].values()),
        "risk_count": payload["at_risk"],
        "safe_count": max(payload["total_students"] - payload["at_risk"], 0)
    }
    return render_template("dashboard.html", data=payload, charts=charts)

@app.route("/students")
def students():
    s, a, m = load_data()
    q = request.args.get("q", "").strip().lower()
    branch = request.args.get("branch", "")
    overview = student_overview(s, a, m, ATTENDANCE_THRESHOLD, PASS_THRESHOLD)
    if q:
        cols = ["name", "roll_number", "student_id", "branch", "division"]
        mask = overview[cols].fillna("").astype(str).apply(lambda col: col.str.lower().str.contains(q, regex=False)).any(axis=1)
        overview = overview[mask]
    if branch:
        overview = overview[overview["branch"] == branch]
    branches = sorted(s["branch"].dropna().unique().tolist()) if not s.empty else []
    page = max(int(request.args.get("page", 1)), 1)
    per_page = 15
    total = len(overview)
    pages = max((total + per_page - 1) // per_page, 1)
    view = overview.iloc[(page-1)*per_page:page*per_page]
    return render_template("students.html", students=view.to_dict("records"), q=q, branch=branch, branches=branches, page=page, pages=pages, total=total)

@app.route("/students/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        s, a, m = load_data()
        row = {c: request.form.get(c, "").strip() for c in STUDENT_COLUMNS}
        if any(not row[c] for c in STUDENT_COLUMNS):
            flash("Please complete every field.", "danger")
        elif row["student_id"] in s["student_id"].astype(str).tolist():
            flash("Student ID already exists.", "danger")
        elif row["roll_number"] in s["roll_number"].astype(str).tolist():
            flash("Roll number already exists.", "danger")
        else:
            s = pd.concat([s, pd.DataFrame([row])], ignore_index=True)
            atomic_write(s[STUDENT_COLUMNS], STUDENTS)
            flash("Student added successfully.", "success")
            return redirect(url_for("students"))
    return render_template("add_student.html", student={})

@app.route("/students/<student_id>")
def student_details(student_id):
    s, a, m = load_data()
    match = s[s["student_id"].astype(str) == student_id]
    if match.empty: abort(404)
    student = match.iloc[0].to_dict()
    att = a[a["student_id"].astype(str) == student_id].to_dict("records")
    marks = m[m["student_id"].astype(str) == student_id].to_dict("records")
    overview = student_overview(match, a, m, ATTENDANCE_THRESHOLD, PASS_THRESHOLD).iloc[0].to_dict()
    return render_template("student_details.html", student=student, attendance=att, marks=marks, overview=overview)

@app.route("/students/<student_id>/delete", methods=["POST"])
def delete_student(student_id):
    s, a, m = load_data()
    if not (s["student_id"].astype(str) == student_id).any(): abort(404)
    atomic_write(s[s["student_id"].astype(str) != student_id][STUDENT_COLUMNS], STUDENTS)
    atomic_write(a[a["student_id"].astype(str) != student_id][ATTENDANCE_COLUMNS], ATTENDANCE)
    atomic_write(m[m["student_id"].astype(str) != student_id][MARK_COLUMNS], MARKS)
    flash("Student and related records deleted.", "success")
    return redirect(url_for("students"))

@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    s, a, m = load_data()
    if request.method == "POST":
        row = {c: request.form.get(c, "").strip() for c in ATTENDANCE_COLUMNS}
        if not all(row.values()):
            flash("Complete all attendance fields.", "danger")
        elif row["student_id"] not in s["student_id"].astype(str).tolist():
            flash("Select a valid student.", "danger")
        elif row["status"] not in ["Present", "Absent"]:
            flash("Status must be Present or Absent.", "danger")
        elif ((a["student_id"].astype(str) == row["student_id"]) & (a["subject"].astype(str) == row["subject"]) & (a["date"].astype(str) == row["date"])).any():
            flash("An attendance record already exists for this student, subject and date.", "danger")
        else:
            a = pd.concat([a, pd.DataFrame([row])], ignore_index=True)
            atomic_write(a[ATTENDANCE_COLUMNS], ATTENDANCE)
            flash("Attendance recorded.", "success")
            return redirect(url_for("attendance"))
    return render_template("attendance.html", students=s.to_dict("records"), attendance=a.tail(100).iloc[::-1].to_dict("records"))

@app.route("/marks", methods=["GET", "POST"])
def marks():
    s, a, m = load_data()
    if request.method == "POST":
        row = {c: request.form.get(c, "").strip() for c in MARK_COLUMNS}
        try:
            obtained, maximum = float(row["marks_obtained"]), float(row["maximum_marks"])
            if not all(row.values()) or maximum <= 0 or obtained < 0 or obtained > maximum:
                raise ValueError
            if row["student_id"] not in s["student_id"].astype(str).tolist(): raise ValueError
        except ValueError:
            flash("Check the student, required fields, and marks range (0 to maximum marks).", "danger")
        else:
            m = pd.concat([m, pd.DataFrame([row])], ignore_index=True)
            atomic_write(m[MARK_COLUMNS], MARKS)
            flash("Marks saved.", "success")
            return redirect(url_for("marks"))
    return render_template("marks.html", students=s.to_dict("records"), marks=m.tail(100).iloc[::-1].to_dict("records"))

@app.route("/analytics")
def analytics():
    s, a, m = load_data()
    data = analytics_payload(s, a, m, ATTENDANCE_THRESHOLD, PASS_THRESHOLD)
    return render_template("analytics.html", data=data)

@app.route("/risk")
def risk_students():
    s, a, m = load_data()
    risks = classify_students(s, a, m, ATTENDANCE_THRESHOLD, PASS_THRESHOLD)
    return render_template("risk_students.html", students=risks.to_dict("records"))

@app.route("/import-export", methods=["GET", "POST"])
def import_export():
    if request.method == "POST":
        kind = request.form.get("kind")
        upload = request.files.get("file")
        mapping = {"students": (STUDENTS, STUDENT_COLUMNS), "attendance": (ATTENDANCE, ATTENDANCE_COLUMNS), "marks": (MARKS, MARK_COLUMNS)}
        if kind not in mapping or not upload or not upload.filename.lower().endswith(".csv"):
            flash("Choose a valid CSV file and data type.", "danger")
        else:
            path, columns = mapping[kind]
            try:
                incoming = pd.read_csv(upload)
                validate_columns(incoming, columns)
                incoming = incoming[columns]
                if incoming.isnull().any().any(): raise ValueError("CSV contains blank required fields.")
                if kind == "students":
                    incoming = validate_student(incoming)
                elif kind == "attendance":
                    if not incoming["status"].isin(["Present", "Absent"]).all(): raise ValueError("Status must be Present or Absent.")
                elif kind == "marks":
                    incoming["marks_obtained"] = pd.to_numeric(incoming["marks_obtained"], errors="raise")
                    incoming["maximum_marks"] = pd.to_numeric(incoming["maximum_marks"], errors="raise")
                    if ((incoming["maximum_marks"] <= 0) | (incoming["marks_obtained"] < 0) | (incoming["marks_obtained"] > incoming["maximum_marks"])).any(): raise ValueError("Invalid marks range.")
                atomic_write(incoming, path)
                flash(f"Imported {len(incoming)} {kind} records. Existing {kind} data was replaced.", "success")
            except Exception as exc:
                flash(f"Import rejected; existing data was not changed. {exc}", "danger")
        return redirect(url_for("import_export"))
    return render_template("import_export.html")

@app.route("/export/<kind>")
def export_csv(kind):
    s, a, m = load_data()
    mapping = {"students": (s, "students.csv"), "attendance": (a, "attendance.csv"), "marks": (m, "marks.csv")}
    if kind == "overview":
        df = student_overview(s, a, m, ATTENDANCE_THRESHOLD, PASS_THRESHOLD).copy()
        df["risk_reasons"] = df["risk_reasons"].apply(lambda x: "; ".join(x))
        filename = "student_overview.csv"
    elif kind in mapping:
        df, filename = mapping[kind]
    else: abort(404)
    buffer = io.BytesIO(df.to_csv(index=False).encode("utf-8-sig"))
    return send_file(buffer, mimetype="text/csv", as_attachment=True, download_name=filename)

@app.route("/reports")
def reports():
    return render_template("reports.html")

@app.route("/health")
def health():
    return {"status": "ok"}

@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", code=404, message="The page or record could not be found."), 404

@app.errorhandler(500)
def server_error(error):
    return render_template("error.html", code=500, message="Something went wrong. Check the terminal for details."), 500

init_data()
if __name__ == "__main__":
    app.run(debug=True)
