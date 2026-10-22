"""A free stand-in for Claude that drafts simple replies, so replies can be tried and tested without an API key.

It copies the best-matching section of the first article it was given, unless the ticket mentions a topic the help
center doesn't cover. Its replies are much less precise than the real AI's.
"""

import re
from types import SimpleNamespace

from src.answer.schema import DraftReply

NOT_COVERED = ["quickbooks", "instagram", "pre-order", "delivery date", "appeal"]


def fake_reply(text: str, chat: bool = False) -> DraftReply:
    name = re.search(r"Merchant: (\S+)", text)
    first = name.group(1) if name else "there"
    subject = re.search(r"Subject: (.+)", text)
    topic = subject.group(1).strip().lower() if subject else "your question"
    articles = re.findall(r'<article id="([^"]+)" title="([^"]+)"', text)
    ticket_text = text.split("Help-center articles")[0].lower()
    opening = (f"Hello {first},\n\nThank you for contacting Storely Support. "
               f"I understand you have a question about {topic}.")
    if chat:
        latest = ticket_text.split("answer the merchant's latest message")[0]
        if not articles or any(w in latest for w in NOT_COVERED):
            return DraftReply(answered=False, cited_articles=[], reply="I will connect you with a specialist.",
                              missing="The fake AI found a topic the help center doesn't cover.")
        greeting = f"Hello {first},\n\n" if "this is your first reply" in ticket_text else ""
        return DraftReply(answered=True, cited_articles=[articles[0][0]], missing="",
                          reply=f"{greeting}Here is how to resolve your {short_topic(topic)} question.\n\n"
                                f"{best_section(text, topic)}")
    if not articles or any(w in ticket_text for w in NOT_COVERED):
        return DraftReply(answered=False, cited_articles=[],
                          reply=f"{opening}\n\nI have forwarded your request to a specialist on our team, "
                                "who will follow up with you directly.",
                          missing="The fake AI found a topic the help center doesn't cover.")
    return DraftReply(answered=True, cited_articles=[articles[0][0]], missing="",
                      reply=f"{opening}\n\n{best_section(text, topic)}\n\n"
                            "If the issue continues, please reply to this message and we will look into it further.")


def best_section(text: str, question: str) -> str:
    """The section of the first article that shares the most words with the question, without its heading."""
    body = re.search(r'<article id="[^"]+" title="[^"]+">\n(.*?)</article>', text, re.S)
    if not body:
        return ""
    words = set(re.findall(r"[a-z0-9$]{3,}", question.lower()))
    sections = [p.strip() for p in re.split(r"^#{2,3} ", body.group(1), flags=re.M)[1:] if p.strip()]
    if not sections:
        return body.group(1).strip()
    best = max(sections, key=lambda p: len(words & set(re.findall(r"[a-z0-9$]{3,}", p.lower()))))
    lines = best.splitlines()[1:]  # drop the heading
    return "\n".join(l for l in lines if l.strip()).replace("**", "").strip()


def short_topic(text: str) -> str:
    """A one-word summary of the question, such as "shipping", so the reply doesn't repeat it word for word."""
    from src.triage.fake_client import fake_triage
    return fake_triage(text).category


class FakeAnswerClient:
    """Implements the one method the reply engine uses: client.messages.parse(...)."""

    def __init__(self):
        self.messages = self
        self.calls = 0

    def parse(self, *, messages, system, **kwargs):
        self.calls += 1
        text = messages[-1]["content"]
        return SimpleNamespace(
            parsed_output=fake_reply(text, chat="live chat" in system),
            stop_reason="end_turn",
            usage=SimpleNamespace(input_tokens=0, output_tokens=0),  # the fake AI is free
        )
