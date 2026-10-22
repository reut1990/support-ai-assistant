"""Reads tickets from HubSpot and writes the AI's results back onto each ticket.

HubSpot is the helpdesk here: tickets live in HubSpot's free Service tools, each linked to the merchant as a contact.
The AI's results are saved as ticket properties in a "Storely AI" group, so an agent sees them in the ticket sidebar.

Help articles still come from Google Drive (or the local files), since HubSpot's knowledge base isn't in the free plan.
The correct labels used to measure accuracy never go into HubSpot; they're matched from data/tickets/tickets.csv.
Setup steps: docs/setup-hubspot.md
"""

import time

from src import config
from src.connectors.base import DataSource
from src.models import ALL_RESULT_COLUMNS, Article, Ticket

API = "https://api.hubapi.com"
GROUP = "storely_ai"
# Ticket fields that HubSpot doesn't have built in, saved as custom properties.
TICKET_FIELDS = ["storely_ticket_id", "storely_created_at", "customer_name", "customer_email",
                 "store_name", "plan", "channel", "chat_outcome"]
LONG_TEXT = {"ai_reason", "ai_reply", "ai_missing", "agent_reply", "chat_outcome"}
# HubSpot's built-in priority, set from the AI's urgency so tickets can be sorted in HubSpot itself.
PRIORITY = {"low": "LOW", "medium": "MEDIUM", "high": "HIGH", "urgent": "HIGH"}
TICKET_TO_CONTACT = 16  # HubSpot's id for the "ticket is linked to contact" association
NEW_STAGE = {"hs_pipeline": "0", "hs_pipeline_stage": "1"}  # default support pipeline, stage "New"
CLOSED_STAGE = {"hs_pipeline": "0", "hs_pipeline_stage": "4"}  # default support pipeline, stage "Closed"


class HubSpotError(Exception):
    pass


class HubSpotClient:
    """A small wrapper around HubSpot's REST API that waits and retries when the rate limit is hit."""

    def __init__(self, token: str | None = None, session=None, sleep=time.sleep):
        token = token or config.HUBSPOT_ACCESS_TOKEN
        if not token:
            raise ValueError("Set HUBSPOT_ACCESS_TOKEN in your .env file. See docs/setup-hubspot.md.")
        if session is None:
            import requests
            session = requests.Session()
        self.session = session
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        self.sleep = sleep

    def call(self, method: str, path: str, json=None, params=None, ok_statuses=(200, 201, 204)):
        for attempt in range(6):
            r = self.session.request(method, API + path, headers=self.headers, json=json, params=params, timeout=30)
            if r.status_code == 429:
                wait = float(r.headers.get("Retry-After", 10 * (attempt + 1)))
                print(f"HubSpot rate limit reached, waiting {wait:.0f} seconds...")
                self.sleep(wait)
                continue
            if r.status_code not in ok_statuses:
                raise HubSpotError(_explain(r))
            return r.json() if r.status_code != 204 and r.content else {}
        raise HubSpotError("HubSpot kept saying the rate limit was reached. Try again in a minute.")

    def list_tickets(self, properties: list[str]) -> list[dict]:
        tickets, after = [], None
        while True:
            params = {"limit": 100, "properties": ",".join(properties)}
            if after:
                params["after"] = after
            page = self.call("GET", "/crm/v3/objects/tickets", params=params)
            tickets += page.get("results", [])
            after = page.get("paging", {}).get("next", {}).get("after")
            if not after:
                return tickets


def _explain(response) -> str:
    try:
        body = response.json()
    except ValueError:
        body = {"message": response.text[:300]}
    message = body.get("message", "")
    if response.status_code == 401:
        return "HubSpot rejected the access token. Check HUBSPOT_ACCESS_TOKEN in .env."
    if response.status_code == 403:
        scopes = body.get("errors", [{}])[0].get("context", {}).get("requiredGranularScopes") if body.get("errors") else None
        hint = f" Add these scopes to the private app: {', '.join(scopes)}." if scopes else ""
        return f"HubSpot says the private app isn't allowed to do this.{hint} ({message})"
    return f"HubSpot error {response.status_code}: {message}"


class HubSpotSource(DataSource):
    name = "hubspot"

    def __init__(self, client: HubSpotClient | None = None, articles_source: DataSource | None = None,
                 labels_source: DataSource | None = None):
        self.client = client or HubSpotClient()
        self._articles_source = articles_source
        self._labels_source = labels_source
        self._ids = None  # storely ticket id -> HubSpot ticket id

    # --- tickets -------------------------------------------------------------
    def _all(self) -> list[dict]:
        records = self.client.list_tickets(["subject", "content", *TICKET_FIELDS, *ALL_RESULT_COLUMNS])
        records = [r for r in records if r["properties"].get("storely_ticket_id")]
        self._ids = {r["properties"]["storely_ticket_id"]: r["id"] for r in records}
        return sorted(records, key=lambda r: r["properties"]["storely_ticket_id"])

    def _all_ids(self) -> list[str]:
        self._all()
        return list(self._ids)

    def list_tickets(self) -> list[Ticket]:
        labels = {t.ticket_id: t.labels for t in self._labels().list_tickets()}
        tickets = []
        for r in self._all():
            p = {k: v or "" for k, v in r["properties"].items()}
            tickets.append(Ticket(
                ticket_id=p["storely_ticket_id"], created_at=p.get("storely_created_at", ""),
                customer_name=p.get("customer_name", ""), customer_email=p.get("customer_email", ""),
                store_name=p.get("store_name", ""), plan=p.get("plan", ""), channel=p.get("channel", ""),
                subject=p.get("subject", ""), body=p.get("content", ""),
                labels=labels.get(p["storely_ticket_id"], {}),
            ))
        return tickets

    def list_results(self, columns: list[str]) -> dict[str, dict]:
        results = {}
        for r in self._all():
            values = {c: r["properties"].get(c) or "" for c in columns}
            if values[columns[0]]:
                results[r["properties"]["storely_ticket_id"]] = values
        return results

    def write_results(self, ticket_id: str, values: dict) -> None:
        if self._ids is None or ticket_id not in self._ids:
            self._all()
        hubspot_id = self._ids.get(ticket_id)
        if hubspot_id is None:
            raise KeyError(f"Ticket {ticket_id} not found in HubSpot.")
        properties = {k: str(v) for k, v in values.items()}
        if values.get("ai_urgency") in PRIORITY:
            properties["hs_ticket_priority"] = PRIORITY[values["ai_urgency"]]
        self.client.call("PATCH", f"/crm/v3/objects/tickets/{hubspot_id}", json={"properties": properties})

    # --- articles and labels come from elsewhere ----------------------------
    def list_articles(self) -> list[Article]:
        return self._articles().list_articles()

    def _articles(self) -> DataSource:
        if self._articles_source is None:
            self._articles_source = backup_source()
        return self._articles_source

    def _labels(self) -> DataSource:
        if self._labels_source is None:
            from src.connectors.local_files import LocalFilesSource
            self._labels_source = LocalFilesSource()
        return self._labels_source


def backup_source() -> DataSource:
    """Google Drive when it's set up, otherwise the files in this repository."""
    if config.GOOGLE_SHEET_ID and config.GOOGLE_DRIVE_FOLDER_ID:
        from src.connectors.google_drive import GoogleDriveSource
        return GoogleDriveSource()
    from src.connectors.local_files import LocalFilesSource
    return LocalFilesSource()


# --- one-time setup: properties, contacts and tickets ----------------------
def create_properties(client: HubSpotClient) -> int:
    """Creates the "Storely AI" property group and its properties. Safe to run again."""
    client.call("POST", "/crm/v3/properties/tickets/groups",
                json={"name": GROUP, "label": "Storely AI", "displayOrder": -1}, ok_statuses=(200, 201, 409))
    created = 0
    for name in TICKET_FIELDS + ALL_RESULT_COLUMNS:
        body = {"name": name, "label": name.replace("_", " ").capitalize(), "groupName": GROUP,
                "type": "string", "fieldType": "textarea" if name in LONG_TEXT else "text"}
        result = client.call("POST", "/crm/v3/properties/tickets", json=body, ok_statuses=(200, 201, 409))
        created += "name" in result
    return created


def upsert_contacts(client: HubSpotClient, tickets: list[Ticket]) -> dict[str, str]:
    """Creates or updates one contact per merchant email. Returns email -> HubSpot contact id."""
    people = {t.customer_email.lower(): t for t in tickets if t.customer_email}
    ids = {}
    emails = list(people)
    for start in range(0, len(emails), 100):
        inputs = []
        for email in emails[start:start + 100]:
            t = people[email]
            first, _, last = t.customer_name.partition(" ")
            inputs.append({"idProperty": "email", "id": email,
                           "properties": {"email": email, "firstname": first, "lastname": last,
                                          "company": t.store_name}})
        result = client.call("POST", "/crm/v3/objects/contacts/batch/upsert", json={"inputs": inputs})
        for r in result.get("results", []):
            ids[r["properties"]["email"].lower()] = r["id"]
    return ids


def create_tickets(client: HubSpotClient, tickets: list[Ticket], contacts: dict[str, str],
                   results: dict[str, dict] | None = None) -> int:
    """Creates tickets in batches of 100, each linked to its merchant. Optionally includes saved AI results."""
    results = results or {}
    inputs = []
    for t in tickets:
        properties = {"subject": t.subject, "content": t.body, **NEW_STAGE,
                      "storely_ticket_id": t.ticket_id, "storely_created_at": t.created_at,
                      "customer_name": t.customer_name, "customer_email": t.customer_email,
                      "store_name": t.store_name, "plan": t.plan, "channel": t.channel}
        saved = {k: v for k, v in results.get(t.ticket_id, {}).items() if v}
        properties.update(saved)
        if saved.get("ai_urgency") in PRIORITY:
            properties["hs_ticket_priority"] = PRIORITY[saved["ai_urgency"]]
        item = {"properties": properties}
        contact = contacts.get(t.customer_email.lower())
        if contact:
            item["associations"] = [{"to": {"id": contact}, "types": [
                {"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": TICKET_TO_CONTACT}]}]
        inputs.append(item)
    for start in range(0, len(inputs), 100):
        client.call("POST", "/crm/v3/objects/tickets/batch/create", json={"inputs": inputs[start:start + 100]})
    return len(inputs)
