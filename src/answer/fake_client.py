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
    earlier = ticket_text.split("answer the merchant's latest message")[0]
    asked_already = "tell me a bit more" in earlier or "reply with the number" in earlier
    numbered = dict(re.findall(r"^(\d)\. (.+)$", text.split("Help-center articles")[0], re.M))
    lines = [numbered.get(l.strip(), l) for l in merchant_lines(text)]  # "2" means the second choice
    question = " ".join(lines) if asked_already else latest
    section, heading, overlap = match_section(text, question)
    if overlap >= 2:
        return ChatReply(answered=True, cited_articles=[articles[0][0]], missing="",
                         reply=opening_line(latest, asked_already) + "\n\n"
                               f"{section}")
    if not asked_already:
        return ChatReply(answered=False, needs_detail=True, cited_articles=[], missing="",
                         reply="Happy to help with that. Which of these do you mean?", options=likely_cases(text, latest))
    return ChatReply(answered=False, cited_articles=[], reply="I will connect you with a specialist.",
                     missing="The fake AI couldn't match the merchant's words to a help-article section.")


def opening_line(latest: str, asked_already: bool) -> str:
    if re.fullmatch(r"\W*\d\W*", latest):
        return "Sure. Here is how to do that:"  # the merchant picked a numbered choice
    return "Thank you, that helps. Here is what to do:" if asked_already else "Here is how to resolve this:"


LOGIN_WORDS = {"login", "log", "sign", "signin", "access", "password", "code", "lock"}


def likely_cases(text: str, question: str) -> list[str]:
    """Up to 3 article sections that fit the question, written the way a merchant would say them."""
    words = set(tokens(question)) - FILLER
    if words & LOGIN_WORDS:
        words |= LOGIN_WORDS  # "cant login" can mean a password, a code or a lock problem
    ranked = sorted(_sections(text), key=lambda p: -len(words & set(tokens(p))))
    return [as_merchant_words(p.splitlines()[0]) for p in ranked[:3]]


def as_merchant_words(heading: str) -> str:
    """A section heading as the merchant would say it: "Two-step verification codes not arriving" ->
    "My two-step verification codes are not arriving"."""
    h = heading.strip()
    h = re.sub(r"^If you think your\b", "I think my", h)
    h = re.sub(r"\byour\b", "my", h)
    if re.match(r"^(Locked|Unable|Stuck)\b", h):
        return "I'm " + h[0].lower() + h[1:]
    m = re.match(r"^(.+?) not (\w+ing)\b(.*)$", h)
    if m:
        return f"My {m.group(1)[0].lower() + m.group(1)[1:]} are not {m.group(2)}{m.group(3)}"
    return h


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
          "doesnt", "cant", "still", "wont", "isnt", "store", "storely", "page", "thing", "something", "anything"}


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
