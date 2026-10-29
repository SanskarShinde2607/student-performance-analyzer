import pandas as pd
import pytest
from services.csv_manager import validate_columns, validate_student, STUDENT_COLUMNS

def test_missing_columns():
    with pytest.raises(ValueError):
        validate_columns(pd.DataFrame({"student_id":["S1"]}), STUDENT_COLUMNS)

def test_duplicate_student_ids():
    df = pd.DataFrame([
        ["S1","1","A","ECE","2","A","a@example.com","9000000001"],
        ["S1","2","B","ECE","2","A","b@example.com","9000000002"]
    ], columns=STUDENT_COLUMNS)
    with pytest.raises(ValueError):
        validate_student(df)
