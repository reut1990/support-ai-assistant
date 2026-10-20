"""Tests for drafting replies from help articles. No real API calls are made, so nothing is charged."""

import csv
import json

import anthropic
import httpx2 as httpx
import pytest

from evaluation import evaluate_answers
from scripts import run_answers
from src.answer.engine import Answerer, check_citations
from src.answer.fake_client import FakeAnswerClient
from src.answer.retrieval import ArticleSearch
from src.answer.schema import DraftReply
from src.connectors.local_files import LocalFilesSource
from src.models import REPLY_COLUMNS, Ticket

SOURCE = LocalFilesSource()
ARTICLES = SOURCE.list_articles()
TICKET = Ticket("T-1", "2026-10-01", "Ana Lopez", "ana@example.com", "Bloom Co", "Basic", "email",
                "Payout late", "My payout never arrived and the bank account is correct.",
                labels={"category": "payments"})


def test_search_finds_the_payout_article_first():
    found = ArticleSearch(ARTICLES).search(f"{TICKET.subject} {TICKET.body}")
    assert found[0].article_id == "KB-201"
    assert len(found) == 3


def test_search_finds_an_article_of_the_right_category_for_most_tickets():
    search = ArticleSearch(ARTICLES)
    tickets = SOURCE.list_tickets()
    hits = sum(any(a.category == t.labels["category"] for a in search.search(f"{t.subject} {t.body}"))
               for t in tickets)
    assert hits >= 90


def test_citations_of_articles_not_given_are_dropped():
    given = ARTICLES[:2]
    draft = DraftReply(answered=True, reply="Hi", cited_articles=["KB-999", given[1].article_id], missing="")
    result, sources, note = check_citations(draft, given)
    assert [a.article_id for a in sources] == [given[1].article_id]
    assert result.answered and note == ""


def test_answer_without_a_real_source_goes_to_a_person():
    draft = DraftReply(answered=True, reply="Hi", cited_articles=["KB-999"], missing="")
    result, sources, note = check_citations(draft, ARTICLES[:3])
    assert not result.answered and sources == [] and "Needs review" in note


def test_fake_answers_and_says_i_dont_know():
    answerer = Answerer(ARTICLES, client=FakeAnswerClient())
    cols = answerer.answer(TICKET).as_columns()
    assert set(cols) == set(REPLY_COLUMNS)
    assert cols["ai_answered"] == "yes" and cols["ai_sources"].startswith("KB-201")
    gap = Ticket("T-2", "", "Bo", "", "", "Basic", "chat", "QuickBooks", "Can I sync with QuickBooks?")
    assert answerer.answer(gap).as_columns()["ai_answered"] == "no"


def _sdk_client(handler):
    return anthropic.Anthropic(api_key="test-key", http_client=httpx.Client(transport=httpx.MockTransport(handler)),
                               max_retries=0)


def test_real_sdk_request_includes_articles_and_no_labels():
    sent = {}

    def handler(request):
        sent.update(json.loads(request.content))
        answer = {"answered": True, "reply": "Hi Ana, here is what to check.\n\nStorely Support",
                  "cited_articles": ["KB-201"], "missing": ""}
        return httpx.Response(200, json={
            "id": "msg_1", "type": "message", "role": "assistant", "model": "claude-haiku-5-5",
            "content": [{"type": "text", "text": json.dumps(answer)}], "stop_reason": "end_turn",
            "stop_sequence": None, "usage": {"input_tokens": 1800, "output_tokens": 400},
        })

    outcome = Answerer(ARTICLES, client=_sdk_client(handler)).answer(TICKET)
    content = sent["messages"][0]["content"]
    assert '<article id="KB-201"' in content and content.count("<article ") == 3
    assert "label" not in content.lower() and "payments" not in content.split("<article")[0]
    assert sent["output_config"]["format"]["type"] == "json_schema"
    assert outcome.as_columns()["ai_sources"] == "KB-201 Payout schedules, delays and bank accounts"


def test_runner_with_fake_ai_writes_replies_and_skips_done(tmp_path, monkeypatch, capsys):
    source = LocalFilesSource(results_csv=tmp_path / "results.csv")
    first = source.list_tickets()[0].ticket_id
    source.write_triage(first, {"ai_category": "billing"})
    monkeypatch.setattr(run_answers, "get_data_source", lambda: source)
    assert run_answers.main(["--fake", "--limit", "3"]) == 0
    rows = {r["ticket_id"]: r for r in csv.DictReader((tmp_path / "results.csv").open())}
    assert len(rows) == 3
    assert rows[first]["ai_category"] == "billing"  # triage results are kept
    assert all(r["ai_reply"] for r in rows.values())
    run_answers.main(["--fake", "--limit", "3"])
    assert "Nothing left to answer" in capsys.readouterr().out


def test_runner_asks_before_spending(monkeypatch, capsys):
    monkeypatch.setattr(run_answers, "get_data_source", lambda: SOURCE)
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    assert run_answers.main(["--limit", "2", "--redo"]) == 0
    out = capsys.readouterr().out
    assert "Estimated cost: $" in out and "Nothing was charged" in out


def test_evaluation_counts_i_dont_know_and_sources():
    tickets = SOURCE.list_tickets()
    by_id = {t.ticket_id: t for t in tickets}
    replies = {
        "T-1057": {"ai_answered": "no", "ai_reply": "Passed on", "ai_sources": "", "ai_missing": "No QuickBooks article"},
        "T-1062": {"ai_answered": "yes", "ai_reply": "Try this", "ai_sources": "KB-601 Apps", "ai_missing": ""},
        "T-1001": {"ai_answered": "yes", "ai_reply": "Refund", "ai_sources": "KB-101 Bill", "ai_missing": ""},
    }
    s = evaluate_answers.compare([by_id[i] for i in replies], replies, ARTICLES)
    assert len(s["gaps_handed_off"]) == 1 and len(s["gaps_answered"]) == 1
    assert len(s["right_source"]) == 1
    assert "1 of 2" in evaluate_answers.build_report(s)
