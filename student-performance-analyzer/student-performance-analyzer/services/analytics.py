import numpy as np
import pandas as pd

def attendance_summary(attendance):
    if attendance.empty:
        return pd.DataFrame(columns=["student_id", "classes", "present", "attendance_pct"])
    a = attendance.copy()
    a["status"] = a["status"].astype(str).str.title()
    a = a[a["status"].isin(["Present", "Absent"])]
    grouped = a.assign(present=(a["status"] == "Present").astype(int)).groupby("student_id").agg(
        classes=("status", "count"), present=("present", "sum")).reset_index()
    grouped["attendance_pct"] = np.where(grouped["classes"] > 0, grouped["present"] / grouped["classes"] * 100, np.nan)
    return grouped

def marks_summary(marks):
    if marks.empty:
        return pd.DataFrame(columns=["student_id", "marks_pct"])
    m = marks.copy()
    m["marks_obtained"] = pd.to_numeric(m["marks_obtained"], errors="coerce")
    m["maximum_marks"] = pd.to_numeric(m["maximum_marks"], errors="coerce")
    m = m[(m["maximum_marks"] > 0) & (m["marks_obtained"] >= 0) & (m["marks_obtained"] <= m["maximum_marks"])]
    if m.empty:
        return pd.DataFrame(columns=["student_id", "marks_pct"])
    m["earned"] = m["marks_obtained"]
    m["maximum"] = m["maximum_marks"]
    out = m.groupby("student_id").agg(earned=("earned", "sum"), maximum=("maximum", "sum")).reset_index()
    out["marks_pct"] = out["earned"] / out["maximum"] * 100
    return out[["student_id", "marks_pct"]]

def student_overview(students, attendance, marks, attendance_threshold=75, pass_threshold=40):
    out = students.copy()
    att = attendance_summary(attendance)
    mk = marks_summary(marks)
    out = out.merge(att, on="student_id", how="left").merge(mk, on="student_id", how="left")
    out["classes"] = out["classes"].fillna(0).astype(int)
    out["present"] = out["present"].fillna(0).astype(int)
    out["attendance_pct"] = out["attendance_pct"].round(1)
    out["marks_pct"] = out["marks_pct"].round(1)
    out["risk_reasons"] = out.apply(lambda r: risk_reasons(r, attendance_threshold, pass_threshold), axis=1)
    out["risk_level"] = out["risk_reasons"].apply(lambda x: "High" if len(x) >= 2 and any("attendance" in z.lower() for z in x) and any("marks" in z.lower() for z in x) else ("Review" if x else "Low"))
    return out

def risk_reasons(row, attendance_threshold=75, pass_threshold=40):
    reasons = []
    att = row.get("attendance_pct")
    marks = row.get("marks_pct")
    if pd.notna(att) and att < attendance_threshold:
        reasons.append(f"Attendance below {attendance_threshold:.0f}%")
    if pd.notna(marks) and marks < pass_threshold:
        reasons.append(f"Overall marks below {pass_threshold:.0f}%")
    return reasons

def analytics_payload(students, attendance, marks, attendance_threshold=75, pass_threshold=40):
    overview = student_overview(students, attendance, marks, attendance_threshold, pass_threshold)
    valid_marks = pd.to_numeric(marks.get("marks_obtained", pd.Series(dtype=float)), errors="coerce")
    valid_max = pd.to_numeric(marks.get("maximum_marks", pd.Series(dtype=float)), errors="coerce")
    ratios = (valid_marks / valid_max * 100).replace([np.inf, -np.inf], np.nan).dropna()
    subject = []
    if not marks.empty and {"subject", "marks_obtained", "maximum_marks"}.issubset(marks.columns):
        tmp = marks.copy()
        tmp["marks_obtained"] = pd.to_numeric(tmp["marks_obtained"], errors="coerce")
        tmp["maximum_marks"] = pd.to_numeric(tmp["maximum_marks"], errors="coerce")
        tmp = tmp[(tmp["maximum_marks"] > 0) & (tmp["marks_obtained"] >= 0) & (tmp["marks_obtained"] <= tmp["maximum_marks"])]
        if not tmp.empty:
            tmp["pct"] = tmp["marks_obtained"] / tmp["maximum_marks"] * 100
            subject = tmp.groupby("subject")["pct"].mean().round(1).sort_values(ascending=False).to_dict()
    return {
        "total_students": int(len(students)),
        "avg_attendance": round(float(overview["attendance_pct"].dropna().mean()), 1) if overview["attendance_pct"].notna().any() else None,
        "avg_marks": round(float(overview["marks_pct"].dropna().mean()), 1) if overview["marks_pct"].notna().any() else None,
        "low_attendance": int((overview["attendance_pct"] < attendance_threshold).sum()),
        "at_risk": int((overview["risk_level"] != "Low").sum()),
        "top_students": overview.sort_values("marks_pct", ascending=False, na_position="last").head(5).to_dict("records"),
        "subject_averages": subject,
        "attendance_buckets": {
            "Below 50%": int((overview["attendance_pct"] < 50).sum()),
            "50–74%": int(((overview["attendance_pct"] >= 50) & (overview["attendance_pct"] < 75)).sum()),
            "75–89%": int(((overview["attendance_pct"] >= 75) & (overview["attendance_pct"] < 90)).sum()),
            "90%+": int((overview["attendance_pct"] >= 90).sum())
        },
        "mark_stats": {
            "mean": round(float(ratios.mean()), 1) if len(ratios) else None,
            "median": round(float(ratios.median()), 1) if len(ratios) else None,
            "min": round(float(ratios.min()), 1) if len(ratios) else None,
            "max": round(float(ratios.max()), 1) if len(ratios) else None,
            "std": round(float(ratios.std()), 1) if len(ratios) > 1 else None
        },
        "overview": overview
    }
