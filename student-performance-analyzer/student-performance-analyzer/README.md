# Student Performance & Attendance Analyzer

A local Flask application for managing fictional student records, recording attendance and marks, identifying records that need teacher review, and exporting CSV reports.

## Features
- Dashboard KPIs and Chart.js charts based on the current CSV files.
- Searchable student directory, student details, add and delete actions.
- Attendance entry with duplicate checks for student + subject + date.
- Marks entry with maximum-mark validation.
- Pandas/NumPy analytics and transparent rule-based academic risk flags.
- CSV import/export, with validation before replacing existing data.
- CSRF protection via Flask-WTF and automated tests.

## Requirements
Python 3.10+ recommended. Core calculations work locally. Bootstrap and Chart.js are loaded from CDNs, so their styling/charts require internet; all core Flask/CSV operations run locally.

## Windows / VS Code setup (PowerShell)
```powershell
cd student-performance-analyzer
py -m venv .venv
```
Activate in PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```
If PowerShell blocks activation, do not change system policy; call the environment's Python directly:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```
Otherwise install and run:
```powershell
python -m pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Tests
```powershell
.\.venv\Scripts\python.exe -m pytest
```

## CSV schemas
- students.csv: `student_id,roll_number,name,branch,semester,division,email,phone`
- attendance.csv: `student_id,subject,date,status`
- marks.csv: `student_id,subject,assessment_type,marks_obtained,maximum_marks,exam_date`

## Important notes
- The app initializes empty CSV files if files do not exist. Sample fictional data is included in this project archive.
- Importing a CSV replaces the selected data file after validation; export your existing file first if you need a backup.
- Risk flags are review recommendations, not predictions or definitive judgments. The configured thresholds are in `config.py`.
- This development server is for local coursework only and is not suitable for public production deployment. Change the secret key and add authentication before any shared deployment.
