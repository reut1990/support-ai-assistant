"""Reads tickets from a Google Sheet and help articles from a Google Drive folder.

The app signs in as a Google Cloud *service account*. You share the Sheet and the
folder with that account's email address, the same way you'd share with a person.
Setup steps: docs/setup-google-drive.md
"""

import time

from src import config
from src.connectors.base import DataSource
from src.models import Article, Ticket, parse_article

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
        self._ws = None
        self._header = None
        self._rows = None  # ticket_id -> sheet row number

    # --- tickets (Google Sheet) -------------------------------------------
    # Google allows about 60 Sheet reads and 60 writes per minute, so the sheet is
    # opened once and each saved result costs a single write.
    def _worksheet(self):
        if self._ws is None:
            self._ws = _with_retry(lambda: self._gc.open_by_key(self.sheet_id).worksheet(TICKETS_TAB))
        return self._ws

    def list_tickets(self) -> list[Ticket]:
        return [Ticket.from_row(row) for row in self._worksheet().get_all_records()]

    def list_results(self, columns: list[str]) -> dict[str, dict]:
        results = {}
        for row in self._worksheet().get_all_records():
            values = {c: str(row.get(c, "")) for c in columns}
            if values[columns[0]]:
                results[str(row["ticket_id"])] = values
        return results

    def write_results(self, ticket_id: str, values: dict) -> None:
        ws = self._worksheet()
        if self._header is None:
            self._header = _with_retry(lambda: ws.row_values(1))
            ids = _with_retry(lambda: ws.col_values(1))
            self._rows = {str(v): i for i, v in enumerate(ids, start=1)}
        missing = [c for c in values if c not in self._header]
        if missing:
            self._header = self._header + missing
            _with_retry(lambda: ws.update([self._header], "A1"))
        row = self._rows.get(ticket_id)
        if row is None:
            raise KeyError(f"Ticket {ticket_id} not found in the sheet.")
        # The columns of one result sit side by side, so they're saved with a single write.
        positions = sorted(self._header.index(c) for c in values)
        first, last = positions[0], positions[-1]
        cells = [str(values.get(c, "")) if c in values else None for c in self._header[first:last + 1]]
        if None in cells:
            raise ValueError("Result columns must sit next to each other in the sheet.")
        _with_retry(lambda: ws.update([cells], f"{_col_letter(first + 1)}{row}"))

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


def _with_retry(call, attempts: int = 6, wait: float = 10.0):
    """Runs a Google call, waiting and retrying when Google says the per-minute limit was hit."""
    for attempt in range(attempts):
        try:
            return call()
        except Exception as e:
            if getattr(e, "code", None) != 429 or attempt == attempts - 1:
                raise
            delay = wait * (attempt + 1)
            print(f"Google rate limit reached, waiting {delay:.0f} seconds...")
            time.sleep(delay)


def _col_letter(n: int) -> str:
    letters = ""
    while n:
        n, rem = divmod(n - 1, 26)
        letters = chr(65 + rem) + letters
    return letters
