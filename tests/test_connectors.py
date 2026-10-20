"""Tests for the data sources. Google is replaced with small fakes, so no account is needed."""

import csv
from types import SimpleNamespace

import pytest

from src.connectors import get_data_source
from src.connectors.google_drive import GOOGLE_DOC, GoogleDriveSource
from src.connectors.local_files import LocalFilesSource
from src.models import AI_COLUMNS, parse_article


# --- local files ------------------------------------------------------------
def test_local_source_reads_sample_data():
    source = LocalFilesSource()
    tickets = source.list_tickets()
    articles = source.list_articles()
    assert len(tickets) == 100
    assert len(articles) == 15
    assert tickets[0].labels.keys() == {"category", "urgency", "sentiment", "churn_risk"}
    assert all(a.article_id.startswith("KB-") for a in articles)


def test_local_source_writes_and_updates_triage(tmp_path):
    source = LocalFilesSource(results_csv=tmp_path / "results.csv")
    source.write_triage("T-1001", {"ai_category": "billing", "ai_urgency": "low"})
    source.write_triage("T-1002", {"ai_category": "domains"})
    source.write_triage("T-1001", {"ai_category": "payments"})
    rows = list(csv.DictReader((tmp_path / "results.csv").open()))
    assert [r["ticket_id"] for r in rows] == ["T-1001", "T-1002"]
    assert rows[0]["ai_category"] == "payments"


def test_parse_article_reads_header():
    a = parse_article("---\nid: KB-1\ntitle: Hello\ncategory: billing\n---\n\n# Hello\nBody", "x.md")
    assert (a.article_id, a.title, a.category, a.source) == ("KB-1", "Hello", "billing", "x.md")
    assert a.body.startswith("# Hello")


def test_factory_rejects_unknown_source():
    with pytest.raises(ValueError):
        get_data_source("dropbox")


# --- Google, with fakes -------------------------------------------------------
class FakeWorksheet:
    def __init__(self, rows):
        self.rows = [list(r) for r in rows]

    def get_all_records(self):
        header = self.rows[0]
        return [dict(zip(header, r)) for r in self.rows[1:]]

    def row_values(self, n):
        return self.rows[n - 1]

    def col_values(self, n):
        return [r[n - 1] for r in self.rows]

    def find(self, value, in_column):
        for i, r in enumerate(self.rows, start=1):
            if r[in_column - 1] == value:
                return SimpleNamespace(row=i)
        return None

    def update(self, values, range_name):
        col = ord(range_name[0]) - 64
        row = int(range_name[1:])
        for r_off, vals in enumerate(values):
            target = self.rows[row - 1 + r_off]
            needed = col - 1 + len(vals)
            target.extend([""] * (needed - len(target)))
            target[col - 1:needed] = vals


class FakeGspread:
    def __init__(self, ws):
        self.ws = ws

    def open_by_key(self, key):
        return SimpleNamespace(worksheet=lambda name: self.ws)


class FakeRequest:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result


class FakeDrive:
    def __init__(self, files, contents):
        self._files, self._contents = files, contents

    def files(self):
        return self

    def list(self, **kwargs):
        return FakeRequest({"files": self._files})

    def export(self, fileId, mimeType):
        return FakeRequest(self._contents[fileId])

    def get_media(self, fileId):
        return FakeRequest(self._contents[fileId])


def make_google_source():
    ws = FakeWorksheet([
        ["ticket_id", "subject", "body", "label_category"],
        ["T-1", "Payout late", "Where is my money", "payments"],
        ["T-2", "SSL", "Not secure warning", "domains"],
    ])
    files = [
        {"id": "a", "name": "payouts.md", "mimeType": "text/markdown"},
        {"id": "b", "name": "SSL help", "mimeType": GOOGLE_DOC},
        {"id": "c", "name": "logo.png", "mimeType": "image/png"},
        {"id": "d", "name": "README.md", "mimeType": "text/markdown"},
    ]
    contents = {
        "a": b"---\nid: KB-201\ntitle: Payouts\ncategory: payments\n---\nBody",
        "b": "﻿---\nid: KB-302\ntitle: SSL\ncategory: domains\n---\nBody".encode("utf-8"),
    }
    source = GoogleDriveSource("sheet", "folder", FakeGspread(ws), FakeDrive(files, contents))
    return source, ws


def test_google_reads_tickets_and_articles():
    source, _ = make_google_source()
    tickets = source.list_tickets()
    assert [t.ticket_id for t in tickets] == ["T-1", "T-2"]
    assert tickets[0].labels == {"category": "payments"}
    articles = source.list_articles()
    assert [a.article_id for a in articles] == ["KB-201", "KB-302"]


def test_google_writes_triage_into_new_columns():
    source, ws = make_google_source()
    source.write_triage("T-2", {"ai_category": "domains", "ai_urgency": "high", "ai_reason": "SSL issue"})
    header = ws.rows[0]
    assert header[-len(AI_COLUMNS):] == AI_COLUMNS
    row = dict(zip(header, ws.rows[2]))
    assert row["ai_category"] == "domains" and row["ai_reason"] == "SSL issue"
    assert ws.rows[1][4:] == [] or all(v == "" for v in ws.rows[1][4:])


def test_google_unknown_ticket_raises():
    source, _ = make_google_source()
    with pytest.raises(KeyError):
        source.write_triage("T-999", {})


def test_google_write_reads_sheet_once_and_retries_rate_limit(monkeypatch):
    source, ws = make_google_source()
    reads = {"n": 0}
    original = ws.col_values

    def counted(n):
        reads["n"] += 1
        return original(n)

    ws.col_values = counted
    failures = {"left": 1}
    original_update = ws.update

    def flaky_update(values, range_name):
        if range_name != "A1" and failures["left"]:
            failures["left"] -= 1
            raise type("APIError", (Exception,), {"code": 429})()
        return original_update(values, range_name)

    ws.update = flaky_update
    monkeypatch.setattr("src.connectors.google_drive.time.sleep", lambda s: None)
    source.write_triage("T-1", {"ai_category": "payments"})
    source.write_triage("T-2", {"ai_category": "domains"})
    assert reads["n"] == 1
    header = ws.rows[0]
    assert dict(zip(header, ws.rows[1]))["ai_category"] == "payments"
    assert dict(zip(header, ws.rows[2]))["ai_category"] == "domains"


def test_google_adds_reply_columns_after_triage_columns():
    source, ws = make_google_source()
    source.write_triage("T-1", {"ai_category": "payments"})
    source.write_reply("T-1", {"ai_answered": "yes", "ai_reply": "Hi", "ai_sources": "KB-201 Payouts"})
    header = ws.rows[0]
    assert header[-4:] == ["ai_answered", "ai_reply", "ai_sources", "ai_missing"]
    row = dict(zip(header, ws.rows[1]))
    assert row["ai_category"] == "payments" and row["ai_reply"] == "Hi"
    assert source.list_replies() == {"T-1": {"ai_answered": "yes", "ai_reply": "Hi",
                                             "ai_sources": "KB-201 Payouts", "ai_missing": ""}}
