"""Tests for the support chat, with the free fake AI. Nothing is charged."""

from pathlib import Path

import pytest

from src.answer.engine import Answerer
from src.answer.fake_client import FakeAnswerClient
from src.chat.agent import RESOLVED, ChatAgent, ChatSession, Merchant
from src.chat.prompt import SYSTEM_PROMPT
from src.chat.tickets import HubSpotChatTickets, LocalChatTickets
from src.connectors.hubspot import HubSpotClient
from src.connectors.local_files import LocalFilesSource
from src.triage.engine import Triager
from src.triage.fake_client import FakeClaudeClient
from tests.test_hubspot import FakeHubSpot

ARTICLES = LocalFilesSource().list_articles()
APP = str(Path(__file__).resolve().parents[1] / "app" / "support_chat.py")


class MemoryTickets:
    name = "memory"

    def __init__(self):
        self.saved = []

    def save(self, session, closed, outcome):
        self.saved.append((session.chat_id, closed, outcome))
        return f"#{len(self.saved)}"


def make_agent(tickets=None):
    tickets = tickets or MemoryTickets()
    answerer = Answerer(ARTICLES, client=FakeAnswerClient(), system_prompt=SYSTEM_PROMPT)
    return ChatAgent(Triager(client=FakeClaudeClient()), answerer, tickets), tickets


def new_session():
    return ChatSession(Merchant("Maya Larsen", "maya@example.com", "Nomad Market", "Grow"))


def test_answers_then_resolves_as_closed_ticket():
    agent, tickets = make_agent()
    s = new_session()
    agent.handle(s, "How do I set up free shipping over $50?")
    reply = s.messages[-1]
    assert reply.answered and reply.sources and reply.text.startswith("Hello Maya")
    assert s.awaiting_feedback and s.triage["ai_category"] == "shipping"
    agent.handle(s, "And what about local pickup?")
    assert not s.messages[-1].text.startswith("Hello")  # greets only once
    agent.resolve(s)
    assert s.status == "resolved" and tickets.saved == [(s.chat_id, True, RESOLVED)]


def test_asking_for_a_person_hands_off_without_an_answer():
    agent, tickets = make_agent()
    s = new_session()
    agent.handle(s, "Can I talk to a human please?")
    assert s.status == "handed_off" and "maya@example.com" in s.messages[-1].text
    assert tickets.saved[0][1] is False and "asked for a person" in tickets.saved[0][2]


def test_urgent_message_is_handed_off_immediately():
    agent, _ = make_agent()
    s = new_session()
    agent.handle(s, "Someone hacked my account and changed my password")
    assert s.status == "handed_off" and "urgent" in s.messages[-1].text
    assert not any(m.answered for m in s.messages)


def test_uncovered_topic_says_i_dont_know():
    agent, _ = make_agent()
    s = new_session()
    agent.handle(s, "Is there a way to sync my orders with QuickBooks?")
    assert s.status == "handed_off" and "don't have enough information" in s.messages[-1].text
    assert s.note_for_agent


def test_offers_a_person_after_three_answers_and_closed_chat_ignores_messages():
    agent, _ = make_agent()
    s = new_session()
    for q in ["How do I add a discount code?", "Where do I set taxes?", "How do I change my theme fonts?"]:
        agent.handle(s, q)
    assert s.offer_person
    agent.hand_off(s, "not_solved")
    count = len(s.messages)
    agent.handle(s, "hello?")
    assert len(s.messages) == count


def test_spending_limit_hands_off():
    agent, _ = make_agent()
    agent.max_cost = 0.0
    s = new_session()
    agent.handle(s, "How do I add a discount code?")
    assert s.status == "handed_off"


def test_local_and_hubspot_ticket_stores(tmp_path):
    agent, _ = make_agent(LocalChatTickets(tmp_path / "chats.csv"))
    s = new_session()
    agent.handle(s, "How do I add a discount code?")
    agent.resolve(s)
    text = (tmp_path / "chats.csv").read_text()
    assert "Closed" in text and RESOLVED in text and "discount code" in text

    fake = FakeHubSpot()
    store = HubSpotChatTickets(HubSpotClient("test-token", session=fake, sleep=lambda x: None))
    agent, _ = make_agent(store)
    s = new_session()
    agent.handle(s, "I want to speak to someone")
    ticket = next(iter(fake.tickets.values()))
    p = ticket["properties"]
    assert s.ticket_id == ticket["id"]
    assert p["hs_pipeline_stage"] == "1" and p["channel"] == "chat" and "speak to someone" in p["content"]
    assert p["chat_outcome"].startswith("handed to a person")
    assert ticket["associations"]


def test_chat_page_runs_in_practice_mode(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr("src.chat.tickets.chat_tickets", lambda: LocalChatTickets(tmp_path / "chats.csv"))
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    at.text_input[0].set_value("Maya Larsen")
    at.text_input[1].set_value("maya@example.com")
    at.text_input[2].set_value("Nomad Market")
    next(b for b in at.button if b.label == "Start chat").click().run()
    at.chat_input[0].set_value("How do I add a discount code?").run()
    assert not at.exception
    at.button(key="solved").click().run()
    assert "Closed" in (tmp_path / "chats.csv").read_text()
