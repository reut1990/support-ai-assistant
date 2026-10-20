"""Prepares tickets and AI results for the agent assist screen. No Streamlit here, so it's easy to test."""

from dataclasses import dataclass

from src.models import ALL_RESULT_COLUMNS, Ticket
from src.triage.routing import ESCALATIONS

URGENCY_ORDER = ["urgent", "high", "medium", "low", ""]
NEEDS_PERSON = "needs a person"
READY = "ready to send"


@dataclass
class TicketView:
    ticket: Ticket
    ai: dict  # every result column, "" when missing

    @property
    def escalated(self) -> bool:
        return self.ai["ai_queue"] == ESCALATIONS

    @property
    def has_draft(self) -> bool:
        return self.ai["ai_answered"] == "yes"

    @property
    def needs_person(self) -> bool:
        if self.ai["agent_status"]:
            return self.ai["agent_status"] == NEEDS_PERSON
        return self.ai["ai_answered"] == "no"

    @property
    def reply_text(self) -> str:
        """The agent's saved version if there is one, otherwise the AI's draft."""
        return self.ai["agent_reply"] or self.ai["ai_reply"]

    @property
    def source_ids(self) -> list[str]:
        return [s.split(" ", 1)[0] for s in self.ai["ai_sources"].split("; ") if s]


def build_views(tickets: list[Ticket], results: dict[str, dict]) -> list[TicketView]:
    views = []
    for t in tickets:
        saved = results.get(t.ticket_id, {})
        views.append(TicketView(t, {c: saved.get(c, "") for c in ALL_RESULT_COLUMNS}))
    # Escalations first, then by urgency, then oldest first.
    return sorted(views, key=lambda v: (not v.escalated, URGENCY_ORDER.index(v.ai["ai_urgency"])
                                        if v.ai["ai_urgency"] in URGENCY_ORDER else 4, v.ticket.created_at))


def summary(views: list[TicketView]) -> dict:
    return {
        "tickets": len(views),
        "escalations": sum(v.escalated for v in views),
        "needs_person": sum(v.needs_person for v in views),
        "drafts": sum(v.has_draft for v in views),
    }


def filter_views(views, queues=(), urgencies=(), only_needs_person=False, text="") -> list[TicketView]:
    text = text.lower().strip()
    return [v for v in views
            if (not queues or v.ai["ai_queue"] in queues)
            and (not urgencies or v.ai["ai_urgency"] in urgencies)
            and (not only_needs_person or v.needs_person)
            and (not text or text in f"{v.ticket.ticket_id} {v.ticket.subject} {v.ticket.body} "
                                      f"{v.ticket.customer_name} {v.ticket.store_name}".lower())]
