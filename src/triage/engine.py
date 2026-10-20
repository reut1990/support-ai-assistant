"""Sends one ticket to Claude and gets back a validated triage result."""

from dataclasses import dataclass

import pydantic

from src.models import Ticket
from src.triage.cost import PRICES, cost_usd
from src.triage.prompt import SYSTEM_PROMPT, ticket_message
from src.triage.routing import route
from src.triage.schema import TriageResult

DEFAULT_MODEL = "claude-haiku-5-5"


class TriageError(Exception):
    pass


@dataclass
class TriageOutcome:
    ticket_id: str
    result: TriageResult
    queue: str
    input_tokens: int
    output_tokens: int
    cost_usd: float

    def as_columns(self) -> dict:
        r = self.result
        return {
            "ai_category": r.category,
            "ai_urgency": r.urgency,
            "ai_sentiment": r.sentiment,
            "ai_churn_risk": r.churn_risk,
            "ai_queue": self.queue,
            "ai_reason": r.reason,
        }


class Triager:
    def __init__(self, client=None, model: str = DEFAULT_MODEL, effort: str = "low"):
        if model not in PRICES:
            raise ValueError(f"No price known for {model}. Add it to src/triage/cost.py first.")
        if client is None:
            import anthropic
            client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
        self.client = client
        self.model = model
        self.effort = effort

    def triage(self, ticket: Ticket) -> TriageOutcome:
        # The ticket's labels (the correct answers) are deliberately never sent.
        message = ticket_message(ticket.subject, ticket.body, ticket.plan, ticket.channel)
        try:
            response = self.client.messages.parse(
                model=self.model,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": message}],
                output_config={"effort": self.effort},
                output_format=TriageResult,
            )
        except pydantic.ValidationError as e:
            # Happens when the model declines (refusal) or stops before finishing its answer.
            raise TriageError(f"{ticket.ticket_id}: no valid answer from the model.") from e
        usage = response.usage
        spent = cost_usd(self.model, usage.input_tokens, usage.output_tokens)
        if response.stop_reason == "refusal":
            raise TriageError(f"{ticket.ticket_id}: the model declined to triage this ticket.")
        result = response.parsed_output
        if result is None:
            raise TriageError(f"{ticket.ticket_id}: no valid answer (stop reason: {response.stop_reason}).")
        queue = route(result.category, result.urgency, result.sentiment, result.churn_risk)
        return TriageOutcome(ticket.ticket_id, result, queue, usage.input_tokens, usage.output_tokens, spent)
