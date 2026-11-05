"""A free stand-in for Claude that drafts simple replies, so replies can be tried and tested without an API key.

It copies the best-matching section of the first article it was given, unless the ticket mentions a topic the help
center doesn't cover. Its replies are much less precise than the real AI's.
"""

import re
from types import SimpleNamespace

from src.answer.retrieval import tokens
from src.answer.schema import ChatReply, DraftReply

NOT_COVERED = ["quickbooks", "instagram", "pre-order", "delivery date", "appeal"]


def fake_reply(text: str, chat: bool = False) -> DraftReply:
    name = re.search(r"Merchant: (\S+)", text)
    first = name.group(1).capitalize() if name else "there"
    subject = re.search(r"Subject: (.+)", text)
    topic = subject.group(1).strip().lower() if subject else "your question"
    articles = re.findall(r'<article id="([^"]+)" title="([^"]+)"', text)
    ticket_text = text.split("Help-center articles")[0].lower()
    opening = (f"Hello {first},\n\nThank you for contacting Storely Support. "
               f"I understand you have a question about {topic}.")
    if chat:
        return fake_chat_reply(text, topic, articles, ticket_text)
    if not articles or any(w in ticket_text for w in NOT_COVERED):
        return DraftReply(answered=False, cited_articles=[],
                          reply=f"{opening}\n\nI have forwarded your request to a specialist on our team, "
                                "who will follow up with you directly.",
                          missing="The fake AI found a topic the help center doesn't cover.")
    return DraftReply(answered=True, cited_articles=[articles[0][0]], missing="",
                      reply=f"{opening}\n\n{best_section(text, topic)}\n\n"
                            "If the issue continues, please reply to this message and we will look into it further.")


def fake_chat_reply(text: str, latest: str, articles: list, ticket_text: str) -> ChatReply:
    """Chat answers: copy the article section that matches the merchant's words, ask when unsure, else hand off."""
    if not articles or any(w in latest for w in NOT_COVERED):
        return ChatReply(answered=False, cited_articles=[], reply="I will connect you with a specialist.",
                         missing="The fake AI found a topic the help center doesn't cover.")
    asked_already = "could you tell me" in ticket_text.split("answer the merchant's latest message")[0]
    question = " ".join(merchant_lines(text)) if asked_already else latest
    section, heading, overlap = match_section(text, question)
    if overlap >= 2:
        return ChatReply(answered=True, cited_articles=[articles[0][0]], missing="",
                         reply=f"Here is what our help article says under \u201c{heading}\u201d.\n\n"
                               f"{section}")
    if not asked_already:
        cases = "\n".join(f"- {h}" for h in section_headings(text)[:4])
        return ChatReply(answered=False, needs_detail=True, cited_articles=[], missing="",
                         reply=f"I would be glad to help. Could you tell me which of these is closest to your "
                               f"problem?\n\n{cases}")
    return ChatReply(answered=False, cited_articles=[], reply="I will connect you with a specialist.",
                     missing="The fake AI couldn't match the merchant's words to a help-article section.")


def merchant_lines(text: str) -> list[str]:
    name = re.search(r"Merchant: ([^(\n]+)", text)
    prefix = (name.group(1).strip() if name else "Merchant") + ": "
    return [l[len(prefix):] for l in text.splitlines() if l.startswith(prefix)]


def _sections(text: str) -> list[str]:
    body = re.search(r'<article id="[^"]+" title="[^"]+">\n(.*?)</article>', text, re.S)
    if not body:
        return []
    return [p.strip() for p in re.split(r"^#{2,3} ", body.group(1), flags=re.M)[1:] if p.strip()]


def section_headings(text: str) -> list[str]:
    return [p.splitlines()[0].strip() for p in _sections(text)]


def match_section(text: str, question: str) -> tuple[str, str, int]:
    """The section of the first article that shares the most words with the question: (body, heading, shared words).
    Words in a section's heading count twice, because the heading says what the section is about."""
    words = set(tokens(question)) - FILLER
    best, score, shared = "", -1, 0
    for p in _sections(text):
        heading = p.splitlines()[0]
        common = words & set(tokens(p))
        s = len(common) + len(words & set(tokens(heading)))
        if s > score:
            best, score, shared = p, s, len(common)
    if not best:
        return "", "", 0
    lines = best.splitlines()
    return "\n".join(l for l in lines[1:] if l.strip()).strip(), lines[0].strip(), shared


# Common words that say nothing about the topic, so "see" alone doesn't match "see who changed what".
FILLER = {"see", "try", "tri", "trying", "tryinh", "want", "need", "know", "like", "help", "way", "use", "work",
          "doesnt", "cant", "wont", "isnt", "store", "storely", "page", "thing", "something", "anything"}


def best_section(text: str, question: str) -> str:
    """The section of the first article that shares the most words with the question, without its heading."""
    body = re.search(r'<article id="[^"]+" title="[^"]+">\n(.*?)</article>', text, re.S)
    if not body:
        return ""
    if not _sections(text):
        return body.group(1).strip()
    return match_section(text, question)[0]

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
