"""Reads data from the files in this repository. Works for anyone, with no accounts needed."""

import csv
from pathlib import Path

from src import config
from src.connectors.base import DataSource
from src.models import AI_COLUMNS, Article, Ticket, parse_article


class LocalFilesSource(DataSource):
    name = "local"

    def __init__(self, tickets_csv: Path = config.LOCAL_TICKETS_CSV,
                 articles_dir: Path = config.LOCAL_ARTICLES_DIR,
                 results_csv: Path = config.LOCAL_RESULTS_CSV):
        self.tickets_csv = Path(tickets_csv)
        self.articles_dir = Path(articles_dir)
        self.results_csv = Path(results_csv)

    def list_tickets(self) -> list[Ticket]:
        with self.tickets_csv.open(encoding="utf-8") as f:
            return [Ticket.from_row(row) for row in csv.DictReader(f)]

    def list_articles(self) -> list[Article]:
        paths = sorted(p for p in self.articles_dir.glob("*.md") if p.name.lower() != "readme.md")
        articles = [parse_article(p.read_text(encoding="utf-8"), p.name) for p in paths]
        return sorted(articles, key=lambda a: a.article_id)

    def write_triage(self, ticket_id: str, result: dict) -> None:
        rows = {}
        if self.results_csv.exists():
            with self.results_csv.open(encoding="utf-8") as f:
                rows = {r["ticket_id"]: r for r in csv.DictReader(f)}
        rows[ticket_id] = {"ticket_id": ticket_id, **{c: result.get(c, "") for c in AI_COLUMNS}}
        self.results_csv.parent.mkdir(parents=True, exist_ok=True)
        with self.results_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["ticket_id", *AI_COLUMNS])
            writer.writeheader()
            writer.writerows(rows.values())
