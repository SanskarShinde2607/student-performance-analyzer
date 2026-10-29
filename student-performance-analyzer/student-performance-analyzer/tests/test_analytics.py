import pandas as pd
from services.analytics import attendance_summary, marks_summary, risk_reasons

def test_attendance_percentage():
    df = pd.DataFrame([{"student_id":"S1","subject":"Math","date":"2026-01-01","status":"Present"},{"student_id":"S1","subject":"Math","date":"2026-01-02","status":"Absent"}])
    result = attendance_summary(df).iloc[0]
    assert result["attendance_pct"] == 50

def test_marks_percentage_weighted_by_maximum():
    df = pd.DataFrame([{"student_id":"S1","subject":"Math","assessment_type":"Internal","marks_obtained":8,"maximum_marks":10,"exam_date":"2026-01-01"},{"student_id":"S1","subject":"Math","assessment_type":"Final","marks_obtained":40,"maximum_marks":50,"exam_date":"2026-02-01"}])
    assert round(marks_summary(df).iloc[0]["marks_pct"], 2) == 80

def test_risk_reasons():
    assert len(risk_reasons({"attendance_pct":60,"marks_pct":35})) == 2

def test_invalid_marks_are_excluded():
    df = pd.DataFrame([{"student_id":"S1","marks_obtained":15,"maximum_marks":10}])
    assert marks_summary(df).empty
