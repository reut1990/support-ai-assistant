"""The two kinds of data the assistant works with: tickets and help articles."""

from dataclasses import dataclass, field

# Columns the AI writes back for each ticket.
AI_COLUMNS = ["ai_category", "ai_urgency", "ai_sentiment", "ai_churn_risk", "ai_queue", "ai_reason"]


@dataclass
class Ticket:
    ticket_id: str
    created_at: str
    customer_name: str
    customer_email: str
    store_name: str
    plan: str
    channel: str
    subject: str
    body: str
    # Correct answers written by a person. Never shown to the AI; used only to measure accuracy.
    labels: dict = field(default_factory=dict)

    @classmethod
    def from_row(cls, row: dict) -> "Ticket":
        row = {k: str(v) for k, v in row.items()}
        labels = {k.removeprefix("label_"): v for k, v in row.items() if k.startswith("label_") and v}
        return cls(
            ticket_id=row["ticket_id"],
            created_at=row.get("created_at", ""),
            customer_name=row.get("customer_name", ""),
            customer_email=row.get("customer_email", ""),
            store_name=row.get("store_name", ""),
            plan=row.get("plan", ""),
            channel=row.get("channel", ""),
            subject=row.get("subject", ""),
            body=row.get("body", ""),
            labels=labels,
        )


@dataclass
class Article:
    article_id: str
    title: str
    category: str
    body: str
    source: str  # file name or Drive file name, for citing


def parse_article(text: str, source: str) -> Article:
    """Parses an article with a simple '---' header block of 'key: value' lines."""
    meta = {}
    body = text.strip()
    if body.startswith("---"):
        _, header, body = body.split("---", 2)
        for line in header.strip().splitlines():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return Article(
        article_id=meta.get("id", source),
        title=meta.get("title", source),
        category=meta.get("category", ""),
        body=body.strip(),
        source=source,
    )
