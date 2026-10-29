from pathlib import Path
import pandas as pd
from .analytics import student_overview

def export_overview(students, attendance, marks, destination, attendance_threshold=75, pass_threshold=40):
    df = student_overview(students, attendance, marks, attendance_threshold, pass_threshold)
    df["risk_reasons"] = df["risk_reasons"].apply(lambda x: "; ".join(x))
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(destination, index=False)
    return destination
