"""A free stand-in for Claude that drafts template replies, so replies can be tried and tested without an API key.

It "answers" from the first article it was given, unless the ticket mentions a topic the help center doesn't cover.
"""

import re
from types import SimpleNamespace

from src.answer.schema import DraftReply

NOT_COVERED = ["quickbooks", "instagram", "pre-order", "delivery date", "appeal"]


def fake_reply(text: str) -> DraftReply:
    name = re.search(r"Merchant: (\S+)", text)
    first = name.group(1) if name else "there"
    articles = re.findall(r'<article id="([^"]+)" title="([^"]+)"', text)
    ticket_text = text.split("Help-center articles")[0].lower()
    if not articles or any(w in ticket_text for w in NOT_COVERED):
        return DraftReply(answered=False, cited_articles=[],
                          reply=f"Hi {first}, thanks for reaching out. I've passed your question to a specialist "
                                "who will follow up with you shortly.\n\nStorely Support",
                          missing="The fake AI found a topic the help center doesn't cover.")
    article_id, title = articles[0]
    return DraftReply(answered=True, cited_articles=[article_id], missing="",
                      reply=f"Hi {first}, thanks for reaching out. Our guide \"{title}\" explains how to handle "
                            "this. (Template reply from the fake AI, no API call.)\n\nStorely Support")


class FakeAnswerClient:
    """Implements the one method the reply engine uses: client.messages.parse(...)."""

    def __init__(self):
        self.messages = self
        self.calls = 0

    def parse(self, *, messages, system, **kwargs):
        self.calls += 1
        text = messages[-1]["content"]
        return SimpleNamespace(
            parsed_output=fake_reply(text),
            stop_reason="end_turn",
            usage=SimpleNamespace(input_tokens=(len(system) + len(text)) // 4, output_tokens=150),
        )
