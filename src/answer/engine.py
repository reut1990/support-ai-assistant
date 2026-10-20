"""Drafts a reply for one ticket: find the best articles, ask Claude, then check its citations."""

from dataclasses import dataclass

import pydantic

from src.answer.prompt import SYSTEM_PROMPT, answer_message
from src.answer.retrieval import ArticleSearch
from src.answer.schema import DraftReply
from src.models import Article, Ticket
from src.triage.cost import PRICES, cost_usd
from src.triage.engine import DEFAULT_MODEL

ARTICLES_PER_TICKET = 3


class AnswerError(Exception):
    pass


@dataclass
class AnswerOutcome:
    ticket_id: str
    result: DraftReply
    sources: list[Article]  # the articles the reply really cites
    searched: list[Article]  # the articles that were sent to the AI
    note: str
    input_tokens: int
    output_tokens: int
    cost_usd: float

    def as_columns(self) -> dict:
        r = self.result
        return {
            "ai_answered": "yes" if r.answered else "no",
            "ai_reply": format_reply(r.reply, self.sources),
            "ai_sources": "; ".join(f"{a.article_id} {a.title}" for a in self.sources),
            "ai_missing": r.missing or self.note,
        }


class Answerer:
    def __init__(self, articles: list[Article], client=None, model: str = DEFAULT_MODEL, effort: str = "low"):
        if model not in PRICES:
            raise ValueError(f"No price known for {model}. Add it to src/triage/cost.py first.")
        if client is None:
            import anthropic
            client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
        self.search = ArticleSearch(articles)
        self.client = client
        self.model = model
        self.effort = effort

    def find_articles(self, ticket: Ticket) -> list[Article]:
        return self.search.search(f"{ticket.subject} {ticket.body}", top=ARTICLES_PER_TICKET)

    def message_for(self, ticket: Ticket) -> str:
        return answer_message(ticket, self.find_articles(ticket))

    def answer(self, ticket: Ticket) -> AnswerOutcome:
        articles = self.find_articles(ticket)
        try:
            response = self.client.messages.parse(
                model=self.model,
                max_tokens=3000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": answer_message(ticket, articles)}],
                output_config={"effort": self.effort},
                output_format=DraftReply,
            )
        except pydantic.ValidationError as e:
            raise AnswerError(f"{ticket.ticket_id}: no valid answer from the model.") from e
        usage = response.usage
        spent = cost_usd(self.model, usage.input_tokens, usage.output_tokens)
        if response.stop_reason == "refusal":
            raise AnswerError(f"{ticket.ticket_id}: the model declined to answer this ticket.")
        result = response.parsed_output
        if result is None:
            raise AnswerError(f"{ticket.ticket_id}: no valid answer (stop reason: {response.stop_reason}).")
        result, sources, note = check_citations(result, articles)
        return AnswerOutcome(ticket.ticket_id, result, sources, articles, note,
                             usage.input_tokens, usage.output_tokens, spent)


def check_citations(result: DraftReply, articles: list[Article]) -> tuple[DraftReply, list[Article], str]:
    """Keeps only citations of articles the AI was actually given. An answer with no real source goes to a person."""
    by_id = {a.article_id: a for a in articles}
    sources = [by_id[i] for i in dict.fromkeys(result.cited_articles) if i in by_id]
    note = ""
    if result.answered and not sources:
        note = "Needs review: the draft didn't cite any of the articles it was given."
        result = result.model_copy(update={"answered": False})
    return result, sources, note


SIGNATURE = "Kind regards,\nStorely Support Team"
CLOSINGS = {"storely support", "storely support team", "best,", "best regards,", "kind regards,", "regards,",
            "thanks,", "thank you,", "sincerely,"}


def format_reply(text: str, sources: list[Article]) -> str:
    """Adds the help-article reference and the signature, so every reply ends the same way."""
    lines = text.strip().splitlines()
    while lines and (not lines[-1].strip() or lines[-1].strip().lower() in CLOSINGS):
        lines.pop()  # drop a closing the AI added anyway
    parts = ["\n".join(lines)]
    if sources:
        titles = [f"\u201c{a.title}\u201d" for a in sources]
        if len(titles) == 1:
            parts.append(f"For more details, please see our help article {titles[0]}.")
        else:
            parts.append(f"For more details, please see our help articles {', '.join(titles[:-1])} and {titles[-1]}.")
    parts.append(SIGNATURE)
    return "\n\n".join(parts)
