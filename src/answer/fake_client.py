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
    subject = re.search(r"Subject: (.+)", text)
    topic = subject.group(1).strip().lower() if subject else "your question"
    articles = re.findall(r'<article id="([^"]+)" title="([^"]+)"', text)
    ticket_text = text.split("Help-center articles")[0].lower()
    opening = (f"Hello {first},\n\nThank you for contacting Storely Support. "
               f"I understand you have a question about {topic}.")
    if not articles or any(w in ticket_text for w in NOT_COVERED):
        return DraftReply(answered=False, cited_articles=[],
                          reply=f"{opening}\n\nI have forwarded your request to a specialist on our team, "
                                "who will follow up with you directly.",
                          missing="The fake AI found a topic the help center doesn't cover.")
    return DraftReply(answered=True, cited_articles=[articles[0][0]], missing="",
                      reply=f"{opening}\n\nThis is a sample reply from the free fake AI. With the real AI, "
                            "the answer and numbered steps appear here.\n\n"
                            "If the issue continues, please reply to this message and we will look into it further.")


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
