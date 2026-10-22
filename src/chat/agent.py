"""The support chat's logic: answer from the help articles, or hand the conversation to a person.

Each merchant message goes through these checks, in order:
1. Did the merchant ask for a person? (plain code, free)
2. Is it urgent, or an angry merchant likely to leave? (AI triage)
3. Do the help articles answer it? (search, then AI answer)
Every chat ends as a ticket: closed when the AI solved it, new when it was handed to a person.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.answer.engine import Answerer, AnswerError
from src.models import Article, Ticket
from src.triage.engine import Triager, TriageError
from src.triage.routing import ESCALATIONS

ASK_FOR_PERSON = re.compile(
    r"\b(human|real person|a person|an agent|live agent|representative|manager|"
    r"(talk|speak|chat) (to|with) (someone|somebody|a|an|your|support))\b", re.IGNORECASE)
FOLLOW_UPS_BEFORE_OFFER = 3
MAX_COST_PER_CHAT = 0.10

RESOLVED = "resolved by AI"
HANDED_OFF = "handed to a person"

HANDOFF_MESSAGES = {
    "asked": "Of course. I have passed your conversation to a specialist on our team, who will follow up with you "
             "by email at {email}.",
    "urgent": "I understand this is urgent. I have passed your conversation to a specialist on our team as a "
              "priority, and they will contact you by email at {email}.",
    "not_covered": "I don't have enough information to answer this correctly, so I have passed your conversation to "
                   "a specialist on our team. They will follow up with you by email at {email}.",
    "not_solved": "I am sorry this didn't solve your problem. I have passed your conversation to a specialist on our "
                  "team, who will follow up with you by email at {email}.",
    "error": "I am having trouble answering right now, so I have passed your conversation to a specialist on our "
             "team. They will follow up with you by email at {email}.",
}
HANDOFF_REASONS = {
    "asked": "The merchant asked for a person.",
    "urgent": "Urgent, or an angry merchant at high risk of leaving: handed off without an AI answer.",
    "not_covered": "The help articles don't cover the question.",
    "not_solved": "The merchant said the AI's answer didn't solve the problem.",
    "error": "The AI couldn't answer (error or spending limit), so the chat was handed off.",
}


@dataclass
class Merchant:
    name: str
    email: str
    store: str
    plan: str

    @property
    def first_name(self) -> str:
        return self.name.split(" ")[0] if self.name else "there"


@dataclass
class Message:
    role: str  # "merchant" or "assistant"
    text: str
    sources: list[Article] = field(default_factory=list)
    answered: bool = False  # True when this assistant message answered from the articles


@dataclass
class ChatSession:
    merchant: Merchant
    chat_id: str = field(default_factory=lambda: "C-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
    messages: list[Message] = field(default_factory=list)
    status: str = "open"  # open, resolved, handed_off
    triage: dict = field(default_factory=dict)
    handoff_reason: str = ""
    note_for_agent: str = ""
    answers_given: int = 0
    cost_usd: float = 0.0
    ticket_id: str = ""

    @property
    def is_open(self) -> bool:
        return self.status == "open"

    @property
    def offer_person(self) -> bool:
        """After a few answers without the merchant saying it's solved, offer a person more clearly."""
        return self.is_open and self.answers_given >= FOLLOW_UPS_BEFORE_OFFER

    @property
    def awaiting_feedback(self) -> bool:
        return self.is_open and bool(self.messages) and self.messages[-1].answered

    def merchant_texts(self) -> list[str]:
        return [m.text for m in self.messages if m.role == "merchant"]

    def transcript(self) -> str:
        names = {"merchant": self.merchant.name or "Merchant", "assistant": "Storely chat assistant"}
        return "\n\n".join(f"{names[m.role]}: {m.text}" for m in self.messages)

    def as_ticket(self) -> Ticket:
        """The conversation as a ticket: the first question is the subject, the whole chat is the body."""
        texts = self.merchant_texts()
        first = texts[0] if texts else "Chat"
        subject = first if len(first) <= 70 else first[:67].rstrip() + "..."
        m = self.merchant
        return Ticket(self.chat_id, self.started_at, m.name, m.email, m.store, m.plan, "chat", subject,
                      self.transcript())


class ChatAgent:
    def __init__(self, triager: Triager, answerer: Answerer, tickets, max_cost: float = MAX_COST_PER_CHAT):
        self.triager = triager
        self.answerer = answerer
        self.tickets = tickets  # where finished chats are saved, see src/chat/tickets.py
        self.max_cost = max_cost

    def handle(self, session: ChatSession, text: str) -> None:
        """Takes one merchant message and adds the assistant's response to the session."""
        if not session.is_open or not text.strip():
            return
        session.messages.append(Message("merchant", text.strip()))

        if ASK_FOR_PERSON.search(text):
            self._triage(session)
            return self.hand_off(session, "asked")
        if session.cost_usd >= self.max_cost:
            return self.hand_off(session, "error")

        if not self._triage(session):
            return self.hand_off(session, "error")
        if session.triage.get("ai_urgency") == "urgent" or session.triage.get("ai_queue") == ESCALATIONS:
            return self.hand_off(session, "urgent")

        try:
            outcome = self.answerer.answer(self._question(session))
        except AnswerError:
            return self.hand_off(session, "error")
        session.cost_usd += outcome.cost_usd
        if not outcome.result.answered:
            session.note_for_agent = outcome.result.missing or outcome.note
            return self.hand_off(session, "not_covered")

        reply = outcome.result.reply.strip()
        if session.answers_given and reply.lower().startswith("hello"):
            reply = reply.split("\n", 1)[-1].strip()  # greet only once per chat
        if outcome.result.missing:
            session.note_for_agent = outcome.result.missing
        session.answers_given += 1
        session.messages.append(Message("assistant", reply, outcome.sources, answered=True))

    def resolve(self, session: ChatSession) -> None:
        """The merchant said the answer solved the problem."""
        if not session.is_open:
            return
        session.status = "resolved"
        session.messages.append(Message("assistant", "I am glad I could help. Thank you for contacting Storely "
                                                     "Support, and have a good day."))
        session.ticket_id = self.tickets.save(session, closed=True, outcome=RESOLVED)

    def hand_off(self, session: ChatSession, reason: str) -> None:
        if not session.is_open:
            return
        session.status = "handed_off"
        session.handoff_reason = HANDOFF_REASONS[reason]
        email = session.merchant.email or "the address on your account"
        session.messages.append(Message("assistant", HANDOFF_MESSAGES[reason].format(email=email)))
        session.ticket_id = self.tickets.save(session, closed=False, outcome=f"{HANDED_OFF}: {session.handoff_reason}")

    def _triage(self, session: ChatSession) -> bool:
        try:
            outcome = self.triager.triage(session.as_ticket())
        except TriageError:
            return False
        session.cost_usd += outcome.cost_usd
        session.triage = outcome.as_columns()
        return True

    def _question(self, session: ChatSession) -> Ticket:
        # The search and the AI focus on the latest message, with the conversation for context.
        ticket = session.as_ticket()
        ticket.subject = session.merchant_texts()[-1]
        ticket.body = ("Conversation so far:\n\n" + session.transcript() +
                       "\n\nAnswer the merchant's latest message." + (" This is your first reply."
                                                                       if not session.answers_given else ""))
        return ticket


def ticket_columns(session: ChatSession, outcome: str) -> dict:
    """The values saved with a finished chat's ticket, using the same columns as the other tickets."""
    t = session.triage
    last_answer = next((m for m in reversed(session.messages) if m.answered), None)
    columns = {
        **{k: v for k, v in t.items() if v},
        "chat_outcome": outcome,
        "ai_answered": "yes" if session.status == "resolved" else "no",
        "ai_missing": session.note_for_agent or session.handoff_reason,
    }
    if last_answer:
        columns["ai_sources"] = "; ".join(f"{a.article_id} {a.title}" for a in last_answer.sources)
    if session.status == "resolved":
        columns["agent_status"] = RESOLVED
    return columns
