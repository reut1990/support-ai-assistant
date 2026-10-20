"""The interface every data source implements, so the rest of the app doesn't care where data lives."""

from abc import ABC, abstractmethod

from src.models import Article, Ticket


class DataSource(ABC):
    name = "base"

    @abstractmethod
    def list_tickets(self) -> list[Ticket]:
        """Returns all tickets."""

    @abstractmethod
    def list_articles(self) -> list[Article]:
        """Returns all help articles."""

    @abstractmethod
    def write_triage(self, ticket_id: str, result: dict) -> None:
        """Saves the AI's triage result for one ticket. Keys are names from models.AI_COLUMNS."""

    @abstractmethod
    def list_triage(self) -> dict[str, dict]:
        """Returns saved triage results as {ticket_id: {ai_column: value}}. Tickets not triaged yet are left out."""
