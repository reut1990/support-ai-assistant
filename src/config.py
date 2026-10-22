"""Settings, read from environment variables or a local .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

DATA_SOURCE = os.getenv("DATA_SOURCE", "local").strip().lower()

LOCAL_TICKETS_CSV = REPO_ROOT / "data" / "tickets" / "tickets.csv"
LOCAL_ARTICLES_DIR = REPO_ROOT / "data" / "help_articles"
LOCAL_RESULTS_CSV = REPO_ROOT / "data" / "output" / "triage_results.csv"

GOOGLE_CREDENTIALS_FILE = Path(
    os.getenv("GOOGLE_CREDENTIALS_FILE", REPO_ROOT / "credentials" / "google-service-account.json")
)
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "").strip()
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "").strip()

HUBSPOT_ACCESS_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN", "").strip()
