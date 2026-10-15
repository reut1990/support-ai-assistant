"""Reads tickets from a Google Sheet and help articles from a Google Drive folder.

The app signs in as a Google Cloud *service account*. You share the Sheet and the
folder with that account's email address, the same way you'd share with a person.
Setup steps: docs/setup-google-drive.md
"""

from src import config
from src.connectors.base import DataSource
from src.models import AI_COLUMNS, Article, Ticket, parse_article

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]
TICKETS_TAB = "Tickets"
GOOGLE_DOC = "application/vnd.google-apps.document"
TEXT_TYPES = ("text/", "application/octet-stream")


class GoogleDriveSource(DataSource):
    name = "google"

    def __init__(self, sheet_id: str | None = None, folder_id: str | None = None,
                 gspread_client=None, drive_service=None):
        self.sheet_id = sheet_id or config.GOOGLE_SHEET_ID
        self.folder_id = folder_id or config.GOOGLE_DRIVE_FOLDER_ID
        if not self.sheet_id or not self.folder_id:
            raise ValueError("Set GOOGLE_SHEET_ID and GOOGLE_DRIVE_FOLDER_ID in your .env file.")
        if gspread_client is None or drive_service is None:
            gspread_client, drive_service = _connect()
        self._gc = gspread_client
        self._drive = drive_service

    # --- tickets (Google Sheet) -------------------------------------------
    def _worksheet(self):
        return self._gc.open_by_key(self.sheet_id).worksheet(TICKETS_TAB)

    def list_tickets(self) -> list[Ticket]:
        return [Ticket.from_row(row) for row in self._worksheet().get_all_records()]

    def write_triage(self, ticket_id: str, result: dict) -> None:
        ws = self._worksheet()
        header = ws.row_values(1)
        missing = [c for c in AI_COLUMNS if c not in header]
        if missing:
            header = header + missing
            ws.update([header], "A1")
        cell = ws.find(ticket_id, in_column=1)
        if cell is None:
            raise KeyError(f"Ticket {ticket_id} not found in the sheet.")
        first = header.index(AI_COLUMNS[0]) + 1
        values = [[result.get(c, "") for c in AI_COLUMNS]]
        ws.update(values, f"{_col_letter(first)}{cell.row}")

    # --- articles (Google Drive folder) -----------------------------------
    def list_articles(self) -> list[Article]:
        articles = []
        for f in self._list_folder():
            name, mime = f["name"], f["mimeType"]
            if name.lower().startswith("readme"):
                continue
            if mime == GOOGLE_DOC:
                raw = self._drive.files().export(fileId=f["id"], mimeType="text/plain").execute()
            elif mime.startswith(TEXT_TYPES) or name.endswith(".md"):
                raw = self._drive.files().get_media(fileId=f["id"]).execute()
            else:
                continue
            text = raw.decode("utf-8-sig") if isinstance(raw, bytes) else raw
            articles.append(parse_article(text, name))
        return sorted(articles, key=lambda a: a.article_id)

    def _list_folder(self) -> list[dict]:
        files, token = [], None
        while True:
            resp = self._drive.files().list(
                q=f"'{self.folder_id}' in parents and trashed = false",
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=token,
            ).execute()
            files += resp.get("files", [])
            token = resp.get("nextPageToken")
            if not token:
                return files


def _connect():
    import gspread
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    path = config.GOOGLE_CREDENTIALS_FILE
    if not path.exists():
        raise FileNotFoundError(f"Google key file not found at {path}. See docs/setup-google-drive.md.")
    creds = Credentials.from_service_account_file(str(path), scopes=SCOPES)
    return gspread.authorize(creds), build("drive", "v3", credentials=creds, cache_discovery=False)


def _col_letter(n: int) -> str:
    letters = ""
    while n:
        n, rem = divmod(n - 1, 26)
        letters = chr(65 + rem) + letters
    return letters
