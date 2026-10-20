"""Tests for the agent assist screen, using local sample data and Streamlit's built-in test runner."""

from pathlib import Path

import pytest

from src.assist import NEEDS_PERSON, READY, build_views, filter_views, summary
from src.connectors.local_files import LocalFilesSource
from src.models import Ticket

APP = str(Path(__file__).resolve().parents[1] / "app" / "agent_assist.py")


def _ticket(i, created="2026-10-01"):
    return Ticket(i, created, "Ana", "", "Bloom", "Basic", "email", f"Subject {i}", "Body")


def test_views_sort_escalations_then_urgency_and_count():
    tickets = [_ticket("T-1"), _ticket("T-2"), _ticket("T-3"), _ticket("T-4")]
    results = {
        "T-1": {"ai_category": "billing", "ai_urgency": "low", "ai_queue": "Billing", "ai_answered": "yes"},
        "T-2": {"ai_category": "themes", "ai_urgency": "high", "ai_queue": "Store Setup", "ai_answered": "no"},
        "T-3": {"ai_category": "account", "ai_urgency": "urgent", "ai_queue": "Priority Escalations",
                "ai_answered": "yes", "agent_status": NEEDS_PERSON},
    }
    views = build_views(tickets, results)
    assert [v.ticket.ticket_id for v in views] == ["T-3", "T-2", "T-1", "T-4"]
    assert summary(views) == {"tickets": 4, "escalations": 1, "needs_person": 2, "drafts": 2}
    assert [v.ticket.ticket_id for v in filter_views(views, only_needs_person=True)] == ["T-3", "T-2"]
    assert [v.ticket.ticket_id for v in filter_views(views, queues=["Billing"])] == ["T-1"]


def test_agent_edit_wins_over_ai_draft():
    views = build_views([_ticket("T-1")], {"T-1": {"ai_category": "billing", "ai_reply": "AI text",
                                                    "agent_reply": "Agent text", "ai_answered": "no",
                                                    "agent_status": READY}})
    assert views[0].reply_text == "Agent text"
    assert not views[0].needs_person  # the agent decided it's ready


@pytest.fixture
def local_source(tmp_path, monkeypatch):
    source = LocalFilesSource(results_csv=tmp_path / "results.csv")
    first = source.list_tickets()[0]
    source.write_triage(first.ticket_id, {"ai_category": "shipping", "ai_urgency": "high", "ai_sentiment": "angry",
                                          "ai_churn_risk": "high", "ai_queue": "Priority Escalations",
                                          "ai_reason": "Labels wrong."})
    source.write_reply(first.ticket_id, {"ai_answered": "yes", "ai_reply": "Hi, here is how.",
                                         "ai_sources": "KB-701 Shipping"})
    monkeypatch.setattr("src.connectors.get_data_source", lambda name=None: source)
    return source, first


def test_screen_shows_ticket_and_saves_agent_reply(local_source):
    from streamlit.testing.v1 import AppTest

    source, first = local_source
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    assert any("Priority Escalation" in e.value for e in at.error)
    assert at.text_area[0].value == "Hi, here is how."
    at.text_area[0].set_value("Hi, edited by the agent.")
    at.button(key="save").click().run()
    assert not at.exception
    saved = source.list_results(["ai_category", "agent_reply", "agent_status"])[first.ticket_id]
    assert saved["agent_reply"] == "Hi, edited by the agent." and saved["agent_status"] == READY
