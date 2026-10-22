"""Tests for the HubSpot connector, against a small in-memory fake of HubSpot's API. No account needed."""

import pytest

from scripts import load_tickets_to_hubspot
from src.connectors.hubspot import HubSpotClient, HubSpotError, HubSpotSource
from src.connectors.local_files import LocalFilesSource
from src.models import AI_COLUMNS


class Response:
    def __init__(self, status, body=None, headers=None):
        self.status_code, self._body, self.headers = status, body or {}, headers or {}
        self.content = b"x" if body is not None else b""
        self.text = str(body)

    def json(self):
        return self._body


class FakeHubSpot:
    """Implements the handful of HubSpot endpoints the connector uses."""

    def __init__(self, page_size=40):
        self.properties, self.groups, self.contacts, self.tickets = set(), set(), {}, {}
        self.calls, self.page_size, self.rate_limit_once = [], page_size, False

    def request(self, method, url, headers=None, json=None, params=None, timeout=None):
        path = url.removeprefix("https://api.hubapi.com")
        self.calls.append((method, path))
        assert headers["Authorization"] == "Bearer test-token"
        if self.rate_limit_once:
            self.rate_limit_once = False
            return Response(429, {}, {"Retry-After": "1"})
        if path == "/crm/v3/properties/tickets/groups":
            if json["name"] in self.groups:
                return Response(409, {"message": "exists"})
            self.groups.add(json["name"])
            return Response(201, json)
        if path == "/crm/v3/properties/tickets":
            if json["name"] in self.properties:
                return Response(409, {"message": "exists"})
            self.properties.add(json["name"])
            return Response(201, json)
        if path == "/crm/v3/objects/contacts/batch/upsert":
            out = []
            for item in json["inputs"]:
                cid = self.contacts.setdefault(item["id"], str(500 + len(self.contacts)))
                out.append({"id": cid, "properties": {"email": item["id"]}})
            return Response(200, {"results": out})
        if path == "/crm/v3/objects/tickets/batch/create":
            for item in json["inputs"]:
                unknown = set(item["properties"]) - self.properties - {"subject", "content", "hs_pipeline",
                                                                        "hs_pipeline_stage", "hs_ticket_priority"}
                assert not unknown, unknown
                tid = str(9000 + len(self.tickets))
                self.tickets[tid] = {"id": tid, "properties": dict(item["properties"]),
                                     "associations": item.get("associations", [])}
            return Response(201, {"results": []})
        if path == "/crm/v3/objects/tickets" and method == "GET":
            ids = sorted(self.tickets)
            start = int(params.get("after", 0))
            page = ids[start:start + self.page_size]
            wanted = params["properties"].split(",")
            results = [{"id": i, "properties": {k: self.tickets[i]["properties"].get(k) for k in wanted}}
                       for i in page]
            body = {"results": results}
            if start + self.page_size < len(ids):
                body["paging"] = {"next": {"after": str(start + self.page_size)}}
            return Response(200, body)
        if path.startswith("/crm/v3/objects/tickets/") and method == "PATCH":
            self.tickets[path.rsplit("/", 1)[1]]["properties"].update(json["properties"])
            return Response(200, {})
        return Response(404, {"message": f"unknown {method} {path}"})


@pytest.fixture
def hubspot(tmp_path):
    fake = FakeHubSpot()
    client = HubSpotClient("test-token", session=fake, sleep=lambda s: None)
    backup = LocalFilesSource(results_csv=tmp_path / "results.csv")
    return fake, client, backup


def test_loader_creates_properties_contacts_and_tickets_and_copies_results(hubspot):
    fake, client, backup = hubspot
    first = backup.list_tickets()[0]
    backup.write_triage(first.ticket_id, {"ai_category": "shipping", "ai_urgency": "urgent", "ai_queue": "X"})
    assert load_tickets_to_hubspot.main([], client=client, source=backup) == 0
    assert len(fake.tickets) == 100
    assert {"storely_ticket_id", "ai_reply", "agent_status"} <= fake.properties
    created = next(t for t in fake.tickets.values() if t["properties"]["storely_ticket_id"] == first.ticket_id)
    assert created["properties"]["ai_category"] == "shipping"
    assert created["properties"]["hs_ticket_priority"] == "HIGH"
    assert created["associations"][0]["types"][0]["associationTypeId"] == 16
    assert not any(k.startswith("label_") for t in fake.tickets.values() for k in t["properties"])

    # Running it again creates nothing new.
    load_tickets_to_hubspot.main([], client=client, source=backup)
    assert len(fake.tickets) == 100


def test_source_reads_tickets_with_labels_and_writes_results(hubspot):
    fake, client, backup = hubspot
    load_tickets_to_hubspot.main(["--without-results"], client=client, source=backup)
    source = HubSpotSource(client=client, articles_source=backup, labels_source=backup)
    tickets = source.list_tickets()
    assert len(tickets) == 100  # read across several pages
    assert tickets[0].labels.keys() == {"category", "urgency", "sentiment", "churn_risk"}
    assert source.list_triage() == {}
    source.write_triage(tickets[0].ticket_id, {"ai_category": "billing", "ai_urgency": "medium"})
    saved = source.list_triage()[tickets[0].ticket_id]
    assert saved["ai_category"] == "billing" and set(saved) == set(AI_COLUMNS)
    patched = next(t for t in fake.tickets.values() if t["properties"]["storely_ticket_id"] == tickets[0].ticket_id)
    assert patched["properties"]["hs_ticket_priority"] == "MEDIUM"
    assert len(source.list_articles()) == 15


def test_rate_limit_is_retried_and_errors_are_explained(hubspot):
    fake, client, _ = hubspot
    fake.rate_limit_once = True
    assert client.list_tickets(["subject"]) == []
    with pytest.raises(HubSpotError, match="unknown"):
        client.call("GET", "/nowhere")


def test_missing_scope_is_explained():
    class Denied:
        def request(self, *a, **k):
            return Response(403, {"message": "denied", "errors": [
                {"context": {"requiredGranularScopes": ["crm.schemas.tickets.write"]}}]})

    with pytest.raises(HubSpotError, match="crm.schemas.tickets.write"):
        HubSpotClient("t", session=Denied()).call("POST", "/crm/v3/properties/tickets", json={})


def test_missing_token_is_explained(monkeypatch):
    monkeypatch.setattr("src.config.HUBSPOT_ACCESS_TOKEN", "")
    with pytest.raises(ValueError, match="HUBSPOT_ACCESS_TOKEN"):
        HubSpotClient()
