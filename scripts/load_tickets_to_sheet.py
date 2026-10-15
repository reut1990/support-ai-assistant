"""Copies data/tickets/tickets.csv into the 'Tickets' tab of your Google Sheet.

Run from the project folder:  python -m scripts.load_tickets_to_sheet
It replaces everything in the 'Tickets' tab, so only run it to (re)load the sample data.
"""

import csv

from src import config
from src.connectors.google_drive import TICKETS_TAB, _connect


def main() -> None:
    with config.LOCAL_TICKETS_CSV.open(encoding="utf-8") as f:
        rows = list(csv.reader(f))
    gc, _ = _connect()
    sheet = gc.open_by_key(config.GOOGLE_SHEET_ID)
    try:
        ws = sheet.worksheet(TICKETS_TAB)
    except Exception:
        ws = sheet.sheet1
        ws.update_title(TICKETS_TAB)
    ws.clear()
    ws.update(rows, "A1")
    ws.freeze(rows=1)
    print(f"Loaded {len(rows) - 1} tickets into '{TICKETS_TAB}' in {sheet.title}.")


if __name__ == "__main__":
    main()
