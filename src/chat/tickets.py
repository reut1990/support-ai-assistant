"""Saves finished chats as tickets: in HubSpot when it's the data source, otherwise in a local file."""

import csv
from pathlib import Path

from src import config
from src.chat.agent import ChatSession, ticket_columns
from src.connectors.hubspot import (CLOSED_STAGE, NEW_STAGE, PRIORITY, TICKET_TO_CONTACT, HubSpotClient,
                                    create_properties, upsert_contacts)

LOCAL_CHAT_TICKETS = config.REPO_ROOT / "data" / "output" / "chat_tickets.csv"
FIELDS = ["ticket_id", "created_at", "status", "chat_outcome", "customer_name", "customer_email", "store_name",
          "plan", "subject", "transcript", "ai_category", "ai_urgency", "ai_sentiment", "ai_churn_risk", "ai_queue",
          "ai_reason", "ai_answered", "ai_sources", "ai_missing", "agent_status"]


class LocalChatTickets:
    name = "local file"

    def __init__(self, path: Path = LOCAL_CHAT_TICKETS):
        self.path = Path(path)

    def save(self, session: ChatSession, closed: bool, outcome: str) -> str:
        t = session.as_ticket()
        row = {"ticket_id": session.chat_id, "created_at": session.started_at, "status": "Closed" if closed else "New",
               "customer_name": t.customer_name, "customer_email": t.customer_email, "store_name": t.store_name,
               "plan": t.plan, "subject": t.subject, "transcript": t.body, **ticket_columns(session, outcome)}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        new_file = not self.path.exists()
        with self.path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
            if new_file:
                writer.writeheader()
            writer.writerow(row)
        return session.chat_id


class HubSpotChatTickets:
    name = "HubSpot"

    def __init__(self, client: HubSpotClient | None = None):
        self.client = client or HubSpotClient()
        self._ready = False

    def save(self, session: ChatSession, closed: bool, outcome: str) -> str:
        if not self._ready:
            create_properties(self.client)  # makes sure the chat_outcome property exists
            self._ready = True
        t = session.as_ticket()
        contacts = upsert_contacts(self.client, [t])
        columns = ticket_columns(session, outcome)
        properties = {"subject": t.subject, "content": t.body, **(CLOSED_STAGE if closed else NEW_STAGE),
                      "storely_ticket_id": session.chat_id, "storely_created_at": session.started_at,
                      "customer_name": t.customer_name, "customer_email": t.customer_email,
                      "store_name": t.store_name, "plan": t.plan, "channel": "chat", **columns}
        if columns.get("ai_urgency") in PRIORITY:
            properties["hs_ticket_priority"] = PRIORITY[columns["ai_urgency"]]
        body = {"properties": properties}
        contact = contacts.get(t.customer_email.lower())
        if contact:
            body["associations"] = [{"to": {"id": contact}, "types": [
                {"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": TICKET_TO_CONTACT}]}]
        created = self.client.call("POST", "/crm/v3/objects/tickets", json=body)
        return created.get("id", session.chat_id)


def chat_tickets():
    if config.DATA_SOURCE == "hubspot":
        return HubSpotChatTickets()
    return LocalChatTickets()
