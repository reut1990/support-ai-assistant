"""The interface every data source implements, so the rest of the app doesn't care where data lives."""

from abc import ABC, abstractmethod

from src.models import AGENT_COLUMNS, AI_COLUMNS, REPLY_COLUMNS, Article, Ticket


class DataSource(ABC):
    name = "base"

    @abstractmethod
    def list_tickets(self) -> list[Ticket]:
        """Returns all tickets."""

    @abstractmethod
    def list_articles(self) -> list[Article]:
        """Returns all help articles."""

    @abstractmethod
    def write_results(self, ticket_id: str, values: dict) -> None:
        """Saves AI output columns for one ticket, adding any columns that don't exist yet."""

    @abstractmethod
    def list_results(self, columns: list[str]) -> dict[str, dict]:
        """Returns {ticket_id: {column: value}} for tickets whose first column is filled in."""

    # Triage results (Step 5), drafted replies (Step 7) and agent edits (Step 8) are separate sets of columns.
    def write_triage(self, ticket_id: str, result: dict) -> None:
        self.write_results(ticket_id, {c: result.get(c, "") for c in AI_COLUMNS})

    def list_triage(self) -> dict[str, dict]:
        return self.list_results(AI_COLUMNS)

    def write_reply(self, ticket_id: str, result: dict) -> None:
        self.write_results(ticket_id, {c: result.get(c, "") for c in REPLY_COLUMNS})

    def list_replies(self) -> dict[str, dict]:
        return self.list_results(REPLY_COLUMNS)

    def write_agent(self, ticket_id: str, values: dict) -> None:
        self.write_results(ticket_id, {c: values.get(c, "") for c in AGENT_COLUMNS})
