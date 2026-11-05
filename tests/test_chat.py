"""Tests for the support chat, with the free fake AI. Nothing is charged."""

from pathlib import Path

import pytest

from src.answer.engine import Answerer
from src.answer.schema import ChatReply
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
    answerer = Answerer(ARTICLES, client=FakeAnswerClient(), system_prompt=SYSTEM_PROMPT, output_format=ChatReply)
    return ChatAgent(Triager(client=FakeClaudeClient()), answerer, tickets), tickets


def new_session():
    return ChatSession(Merchant("Maya Larsen", "maya@example.com", "Nomad Market", "Grow"))


def test_answers_then_resolves_as_closed_ticket():
    agent, tickets = make_agent()
    s = new_session()
    agent.handle(s, "How do I set up free shipping over $50?")
    reply = s.messages[-1]
    assert reply.answered and reply.sources and not reply.text.startswith("Hello")  # the page already greets
    assert s.awaiting_feedback and s.triage["ai_category"] == "shipping"
    agent.handle(s, "And what about local pickup?")
    assert not s.messages[-1].text.startswith("Hello")
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


def test_follow_up_on_a_new_topic_finds_its_own_article():
    agent, _ = make_agent()
    s = new_session()
    agent.handle(s, "How do I offer free shipping on orders over $50?")
    agent.handle(s, "How do I add a discount code?")
    assert [a.article_id for a in s.messages[-1].sources] == ["KB-401"]
    assert "fake AI" not in s.messages[-1].text


def test_assistant_words_do_not_make_the_chat_urgent():
    # Reut's test chat: the assistant's own reply said "immediately", which made the follow-up look urgent.
    agent, _ = make_agent()
    s = new_session()
    agent.handle(s, "i can't login, my two-step verification codes are not arriving")
    assert s.is_open and s.messages[-1].answered
    agent.handle(s, "what if I lost my phone and backup codes")
    assert s.triage["ai_urgency"] != "urgent"


def test_angry_merchant_still_gets_an_answer_and_can_ask_for_a_person():
    agent, _ = make_agent()
    s = new_session()
    agent.handle(s, "This is unacceptable, how do I add a discount code??")
    assert s.is_open and s.messages[-1].answered
    assert s.triage["ai_queue"] == "Priority Escalations"  # still flagged for the ticket


def test_chat_reply_layout():
    from src.chat.formatting import format_chat_reply

    text = format_chat_reply("Hello Reut,\nTo regain access: 1. Use **Forgot password**. 2. Use the "
                             "**Can't access your account?** form.\nThese requests are handled first.")
    assert text == ("Hello Reut,\n\nTo regain access:\n\n1. Use **Forgot password**.\n"
                    "2. Use the **Can't access your account?** form.\n\nThese requests are handled first.")
    assert format_chat_reply("Prices from $0 to $49.99 apply.") == "Prices from $0 to $49.99 apply."



def test_push_back_hands_off_instead_of_repeating():
    # Reut's test: "dont lock anything" after the hacked-account steps got the same steps again.
    agent, tickets = make_agent()
    s = new_session()
    agent.handle(s, "Someone changed my login password, how do I secure my account?")
    assert s.messages[-1].answered
    agent.handle(s, "dont lock anything")
    assert s.status == "handed_off" and s.messages[-1].text.startswith("I understand.")
    assert sum(m.answered for m in s.messages) == 1 and tickets.saved[-1][1] is False


def test_same_answer_twice_hands_off():
    agent, _ = make_agent()
    s = new_session()
    agent.handle(s, "How do I set up free shipping over $50?")
    first = s.messages[-1].text
    agent.answerer.answer = lambda *a, **k: _same(first, k)
    agent.handle(s, "ok and then?")
    assert s.status == "handed_off" and "same steps" in s.messages[-1].text


def _same(text, _):
    from types import SimpleNamespace
    from src.answer.schema import DraftReply
    return SimpleNamespace(result=DraftReply(answered=True, cited_articles=[], reply=text, missing=""),
                           sources=[], cost_usd=0.0, note="")


def test_vague_message_gets_a_question_before_any_hand_off():
    # Reut's test: "cant log in" was handed to a person without even asking what happens.
    agent, _ = make_agent()
    s = new_session()
    agent.handle(s, "cant log in")
    question = s.messages[-1]
    assert s.is_open and "?" in question.text and not question.answered
    assert "\n2. I'm locked out after resetting my password" in question.text  # numbered, in the merchant's words
    agent.handle(s, "it says my account is locked after I reset my password")
    reply = s.messages[-1]
    assert reply.answered and "30 minutes" in reply.text and not reply.text.startswith("Hello")
    assert [a.article_id for a in reply.sources] == ["KB-801"]


def test_ai_says_not_covered_for_vague_message_still_asks(monkeypatch):
    from types import SimpleNamespace
    from src.answer.schema import ChatReply
    agent, _ = make_agent()
    no = SimpleNamespace(result=ChatReply(answered=False, cited_articles=[], reply="I will connect you.",
                                          missing="unclear"), sources=[], cost_usd=0.0, note="")
    agent.answerer.answer = lambda *a, **k: no
    s = new_session()
    agent.handle(s, "cant log in")
    assert s.is_open and "tell me a little more" in s.messages[-1].text
    agent.handle(s, "help")
    assert s.is_open  # second question
    agent.handle(s, "still")
    assert s.status == "handed_off"  # after two questions, a person takes over


def test_not_you_means_the_merchant_wants_a_person():
    # Reut's test: "not you" got another AI answer instead of a person.
    agent, _ = make_agent()
    s = new_session()
    agent.handle(s, "i cant log in")
    agent.handle(s, "not you")
    assert s.status == "handed_off" and s.handoff_reason.startswith("The merchant asked for a person")


def test_replies_never_greet_again():
    from src.chat.agent import _drop_greeting
    assert _drop_greeting("Hello vcxv,\n\nCould you tell me more?") == "Could you tell me more?"
    assert _drop_greeting("Hello, I see.") == "Hello, I see."


def test_merchant_can_pick_a_choice_by_number():
    agent, _ = make_agent()
    s = new_session()
    agent.handle(s, "cant login")
    agent.handle(s, "2")
    assert s.messages[-2].text == "2"  # shown as typed
    assert s.messages[-1].answered and "30 minutes" in s.messages[-1].text


def test_none_of_these_asks_once_more_then_hands_off():
    # Reut's test: "no" to the choices.
    agent, _ = make_agent()
    s = new_session()
    agent.handle(s, "cant login")
    agent.handle(s, "no")
    assert s.is_open and "tell me a little more" in s.messages[-1].text
    agent.handle(s, "none of the above")
    assert s.status == "handed_off"
