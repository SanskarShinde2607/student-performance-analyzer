from .analytics import student_overview

def classify_students(students, attendance, marks, attendance_threshold=75, pass_threshold=40):
    """Transparent rule-based flags for teacher review; not a prediction of failure."""
    overview = student_overview(students, attendance, marks, attendance_threshold, pass_threshold)
    return overview[overview["risk_level"] != "Low"].copy()
