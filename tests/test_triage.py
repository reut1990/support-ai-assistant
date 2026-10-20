"""Tests for the triage engine. No real API calls are made, so nothing is charged."""

import json

import anthropic
import httpx2 as httpx
import pytest

from scripts import run_triage
from src.connectors.local_files import LocalFilesSource
from src.models import Ticket
from src.triage.cost import cost_usd, estimate_run
from src.triage.engine import Triager, TriageError
from src.triage.fake_client import FakeClaudeClient
from src.triage.prompt import SYSTEM_PROMPT
from src.triage.routing import ESCALATIONS, route

TICKET = Ticket("T-1", "2026-10-01", "Ana", "ana@example.com", "Bloom Co", "Basic", "email",
                "Payout late", "My payout never arrived and I need it today.",
                labels={"category": "payments"})


def test_routing_rules():
    assert route("billing", "low", "neutral", "low") == "Billing"
    assert route("domains", "high", "frustrated", "medium") == "Technical"
    assert route("themes", "urgent", "neutral", "low") == ESCALATIONS
    assert route("billing", "medium", "angry", "high") == ESCALATIONS


def test_cost_maths():
    assert cost_usd("claude-haiku-5-5", 1_000_000, 0) == pytest.approx(0.10)
    assert cost_usd("claude-haiku-5-5", 0, 1_000_000) == pytest.approx(0.50)
    # 10 tickets on Haiku should cost about a cent or less.
    assert estimate_run("claude-haiku-5-5", SYSTEM_PROMPT, ["x" * 400] * 10) < 0.01


def test_fake_client_triage_and_columns():
    outcome = Triager(client=FakeClaudeClient()).triage(TICKET)
    cols = outcome.as_columns()
    assert cols["ai_category"] == "payments"
    assert set(cols) == {"ai_category", "ai_urgency", "ai_sentiment", "ai_churn_risk", "ai_queue", "ai_reason"}


def test_unknown_model_is_rejected():
    with pytest.raises(ValueError):
        Triager(client=FakeClaudeClient(), model="claude-made-up")


def _sdk_client(handler):
    """A real Anthropic SDK client whose network is replaced by `handler`."""
    return anthropic.Anthropic(api_key="test-key", http_client=httpx.Client(transport=httpx.MockTransport(handler)),
                               max_retries=0)


def _api_response(text, stop_reason="end_turn"):
    return httpx.Response(200, json={
        "id": "msg_1", "type": "message", "role": "assistant", "model": "claude-haiku-5-5",
        "content": [{"type": "text", "text": text}], "stop_reason": stop_reason, "stop_sequence": None,
        "usage": {"input_tokens": 900, "output_tokens": 150},
    })


def test_real_sdk_request_shape_and_parsing():
    sent = {}

    def handler(request):
        sent.update(json.loads(request.content))
        return _api_response(json.dumps({"category": "payments", "urgency": "high", "sentiment": "frustrated",
                                         "churn_risk": "medium", "reason": "Payout missing, needed today."}))

    outcome = Triager(client=_sdk_client(handler)).triage(TICKET)
    assert sent["model"] == "claude-haiku-5-5"
    assert sent["output_config"]["effort"] == "low"
    assert sent["output_config"]["format"]["type"] == "json_schema"
    assert "payments" in json.dumps(sent["output_config"]["format"]["schema"])
    assert "label" not in sent["messages"][0]["content"].lower()  # correct answers are never sent
    assert outcome.queue == "Payments"
    assert outcome.cost_usd == pytest.approx(cost_usd("claude-haiku-5-5", 900, 150))


def test_refusal_raises():
    client = _sdk_client(lambda r: _api_response("", stop_reason="refusal"))
    with pytest.raises(TriageError):
        Triager(client=client).triage(TICKET)


def test_runner_fake_mode_writes_results(tmp_path, monkeypatch, capsys):
    source = LocalFilesSource(results_csv=tmp_path / "results.csv")
    monkeypatch.setattr(run_triage, "get_data_source", lambda: source)
    assert run_triage.main(["--fake", "--limit", "5"]) == 0
    out = capsys.readouterr().out
    assert "Triaged 5 tickets" in out and "$0.00" in out
    assert len((tmp_path / "results.csv").read_text().strip().splitlines()) == 6


def test_runner_real_mode_cancels_without_spending(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    monkeypatch.setattr(run_triage, "Triager", lambda **kw: pytest.fail("must not create a real client"))
    assert run_triage.main(["--limit", "10"]) == 0
    out = capsys.readouterr().out
    assert "Estimated cost: $0.00" in out and "Nothing was charged" in out
