"""Reads data from the files in this repository. Works for anyone, with no accounts needed."""

import csv
from pathlib import Path

from src import config
from src.connectors.base import DataSource
from src.models import ALL_RESULT_COLUMNS, Article, Ticket, parse_article


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

    def _read_results(self) -> dict[str, dict]:
        if not self.results_csv.exists():
            return {}
        with self.results_csv.open(encoding="utf-8") as f:
            return {r["ticket_id"]: r for r in csv.DictReader(f)}

    def list_results(self, columns: list[str]) -> dict[str, dict]:
        rows = self._read_results()
        return {tid: {c: r.get(c) or "" for c in columns} for tid, r in rows.items() if r.get(columns[0])}

    def write_results(self, ticket_id: str, values: dict) -> None:
        rows = self._read_results()
        rows.setdefault(ticket_id, {"ticket_id": ticket_id}).update({k: str(v) for k, v in values.items()})
        fields = ["ticket_id", *ALL_RESULT_COLUMNS]
        fields += [k for r in rows.values() for k in r if k not in fields]
        self.results_csv.parent.mkdir(parents=True, exist_ok=True)
        with self.results_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(dict.fromkeys(fields)), restval="")
            writer.writeheader()
            writer.writerows(rows.values())
