from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
SECRET_KEY = "local-college-project-change-this-before-deployment"
ATTENDANCE_THRESHOLD = 75.0
PASS_THRESHOLD = 40.0
MAX_CONTENT_LENGTH = 5 * 1024 * 1024
