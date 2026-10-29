import os
import tempfile
from pathlib import Path
import pandas as pd

STUDENT_COLUMNS = ["student_id", "roll_number", "name", "branch", "semester", "division", "email", "phone"]
ATTENDANCE_COLUMNS = ["student_id", "subject", "date", "status"]
MARK_COLUMNS = ["student_id", "subject", "assessment_type", "marks_obtained", "maximum_marks", "exam_date"]

def read_csv(path, columns):
    path = Path(path)
    if not path.exists():
        return pd.DataFrame(columns=columns)
    try:
        df = pd.read_csv(path, dtype={"student_id": str, "roll_number": str})
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=columns)
    for col in columns:
        if col not in df.columns:
            df[col] = pd.NA
    return df[columns]

def atomic_write(df, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.stem, suffix=".tmp", dir=path.parent)
    os.close(fd)
    try:
        df.to_csv(temp_name, index=False)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)

def validate_columns(df, required):
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

def import_csv(upload, destination, required):
    df = pd.read_csv(upload)
    validate_columns(df, required)
    if df[required].isnull().any().any():
        raise ValueError("Required fields contain blank values.")
    atomic_write(df[required], destination)
    return len(df)

def validate_student(df):
    validate_columns(df, STUDENT_COLUMNS)
    if df[STUDENT_COLUMNS].isnull().any().any():
        raise ValueError("All student fields are required.")
    df = df.copy()
    df["student_id"] = df["student_id"].astype(str).str.strip()
    df["roll_number"] = df["roll_number"].astype(str).str.strip()
    if df["student_id"].duplicated().any():
        raise ValueError("Duplicate student IDs found.")
    if df["roll_number"].duplicated().any():
        raise ValueError("Duplicate roll numbers found.")
    return df[STUDENT_COLUMNS]
