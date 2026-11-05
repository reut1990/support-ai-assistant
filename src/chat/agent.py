"""The support chat's logic: answer from the help articles, or hand the conversation to a person.

Each merchant message goes through these checks, in order:
1. Did the merchant ask for a person, or reject the answer they were just given? (plain code)
2. Is it urgent, such as a hacked account or a store that is down? (AI triage of the merchant's words only)
3. Do the help articles answer it? (search, then AI answer). If not, or the message is too vague, ask for more
   detail (up to twice) before handing off.
4. Is the answer new? Sending the same steps twice means they didn't help, so a person takes over.
Every chat ends as a ticket: closed when the AI solved it, new when it was handed to a person.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher

from src.answer.engine import Answerer, AnswerError
from src.answer.retrieval import tokens
from src.chat.formatting import format_chat_reply
from src.models import Article, Ticket
from src.triage.engine import Triager, TriageError

ASK_FOR_PERSON = re.compile(
    r"\b(human|real person|a person|person please|an agent|live agent|representative|manager|someone real|"
    r"(talk|speak|chat) (to|with) (someone|somebody|a|an|your|support)|"
    r"not (you|a bot|the bot|a robot|ai|an ai)|no (bot|bots|robot|ai)|stop the bot)\b", re.IGNORECASE)
# The merchant rejects the answer they were just given: "dont lock anything", "no, that didn't work".
PUSH_BACK = re.compile(
    r"^\W*(no\b|nope|don'?t|do not|didn'?t|did not|doesn'?t|does not|that'?s not|not what|wrong|"
    r"i don'?t want|i do not want|still (not|doesn'?t|can'?t|isn'?t))", re.IGNORECASE)
NONE_OF_THESE = re.compile(r"\W*(no|nope|none|neither|nothing|other|something else|still no|no\W+none of (the above|"
                           r"these|them)|none of (the above|these|them)|not (that|those|these|really))\W*",
                           re.IGNORECASE)
YES = re.compile(r"\W*(yes|yeah|yep|sure|ok|okay|please|yes please|please do|connect me|go ahead)\W*", re.IGNORECASE)
NO = re.compile(r"\W*(no|nope|no thanks|no thank you|not now|not yet|no need)\W*", re.IGNORECASE)
OFFER_QUESTION = "Would you like me to connect you with a specialist on our team who can help with this?"
# The merchant drops the last question and asks something new.
TOPIC_CHANGE = re.compile(r"^\W*(never ?mind|nvm|forget (it|that|about it)|actually|another question|different "
                          r"question|something else|ok(ay)? (and|so)|anyway)\b\W*", re.IGNORECASE)
# Questions about Storely itself, not about the merchant's own products: "what do you offer", "your services".
ABOUT_STORELY = re.compile(r"\b(your|you guys'?|storely'?s?) (products|services|features|platform|company)\b|"
                           r"\bwhat (do|does|can) (you|storely) (offer|do|sell)\b|\babout (you|storely)\b|"
                           r"\bwhat is storely\b", re.IGNORECASE)
FOLLOW_UPS_BEFORE_OFFER = 3
SHORT_MESSAGE_WORDS = 4  # fewer search words than this is too vague to hand off on
MAX_CLARIFYING_QUESTIONS = 3  # per topic: ask for more detail at most 3 times before offering a person
CHOICE_QUESTION = "Happy to help with that. Which of these do you mean?"
CHOICE_FOOTER = "Just reply with the number, or tell me in your own words."
OPEN_QUESTION = ("Happy to help. Could you tell me a bit more about what you need? For example, what you were "
                 "trying to do and any message you see.")
CLARIFY_FALLBACK = ("No problem, let's try another way. Could you tell me a bit more about what you need? For "
                    "example, what you were trying to do and any message you see.")
MAX_COST_PER_CHAT = 0.10
REPEAT_SIMILARITY = 0.8  # a new answer this close to the previous one is a repeat

RESOLVED = "resolved by AI"
HANDED_OFF = "handed to a person"

HANDOFF_MESSAGES = {
    "asked": "Of course. I have passed your conversation to a specialist on our team, who will follow up with you "
             "by email at {email}.",
    "urgent": "I understand this is urgent. I have passed your conversation to a specialist on our team as a "
              "priority, and they will contact you by email at {email}.",
    "not_covered": "Thank you for bearing with me. This needs a closer look than I can give you here, so I have "
                   "passed your conversation to a specialist on our team. They will follow up with you by email at "
                   "{email}.",
    "not_solved": "I am sorry this didn't solve your problem. I have passed your conversation to a specialist on our "
                  "team, who will follow up with you by email at {email}.",
    "pushed_back": "I understand. I have passed your conversation to a specialist on our team, who can look at your "
                   "situation and will follow up with you by email at {email}.",
    "repeat": "I don't want to send you the same steps again, so I have passed your conversation to a specialist on "
              "our team, who will follow up with you by email at {email}.",
    "error": "I am having trouble answering right now, so I have passed your conversation to a specialist on our "
             "team. They will follow up with you by email at {email}.",
}
HANDOFF_REASONS = {
    "asked": "The merchant asked for a person.",
    "urgent": "Urgent (for example a hacked account or a store that is down): handed off without an AI answer.",
    "not_covered": "The help articles don't cover the question.",
    "not_solved": "The merchant said the AI's answer didn't solve the problem.",
    "pushed_back": "The merchant rejected the AI's answer, so a person should take over.",
    "repeat": "The merchant's follow-up got the same answer as before, so a person should take over.",
    "error": "The AI couldn't answer (error or spending limit), so the chat was handed off.",
}


@dataclass
class Merchant:
    name: str
    email: str
    store: str
    plan: str

    @property
    def first_name(self) -> str:
        return self.name.split(" ")[0].capitalize() if self.name else "there"


@dataclass
class Message:
    role: str  # "merchant" or "assistant"
    text: str
    sources: list[Article] = field(default_factory=list)
    answered: bool = False  # True when this assistant message answered from the articles
    offer: bool = False  # True when this assistant message offers to connect the merchant with a person


@dataclass
class ChatSession:
    merchant: Merchant
    chat_id: str = field(default_factory=lambda: "C-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
    messages: list[Message] = field(default_factory=list)
    status: str = "open"  # open, resolved, handed_off
    triage: dict = field(default_factory=dict)
    handoff_reason: str = ""
    note_for_agent: str = ""
    answers_given: int = 0
    questions_asked: int = 0  # clarifying questions the assistant asked
    options: list[str] = field(default_factory=list)  # the choices in the last clarifying question
    picked: str = ""  # the choice the merchant picked by number in their latest message
    topic_start: int = 0  # index of the merchant message where the current topic started
    cost_usd: float = 0.0
    ticket_id: str = ""

    @property
    def is_open(self) -> bool:
        return self.status == "open"

    @property
    def offer_person(self) -> bool:
        """After a few answers without the merchant saying it's solved, offer a person more clearly."""
        return self.is_open and self.answers_given >= FOLLOW_UPS_BEFORE_OFFER

    @property
    def awaiting_offer(self) -> bool:
        return self.is_open and bool(self.messages) and self.messages[-1].offer

    @property
    def awaiting_feedback(self) -> bool:
        return self.is_open and bool(self.messages) and self.messages[-1].answered

    def merchant_texts(self) -> list[str]:
        return [m.text for m in self.messages if m.role == "merchant"]

    def transcript(self) -> str:
        names = {"merchant": self.merchant.name or "Merchant", "assistant": "Storely chat assistant"}
        return "\n\n".join(f"{names[m.role]}: {m.text}" for m in self.messages)

    def as_ticket(self) -> Ticket:
        """The conversation as a ticket: the first question is the subject, the whole chat is the body."""
        texts = self.merchant_texts()
        first = texts[0] if texts else "Chat"
        subject = first if len(first) <= 70 else first[:67].rstrip() + "..."
        m = self.merchant
        return Ticket(self.chat_id, self.started_at, m.name, m.email, m.store, m.plan, "chat", subject,
                      self.transcript())


class ChatAgent:
    def __init__(self, triager: Triager, answerer: Answerer, tickets, max_cost: float = MAX_COST_PER_CHAT):
        self.triager = triager
        self.answerer = answerer
        self.tickets = tickets  # where finished chats are saved, see src/chat/tickets.py
        self.max_cost = max_cost

    def handle(self, session: ChatSession, text: str) -> None:
        """Takes one merchant message and adds the assistant's response to the session."""
        if not session.is_open or not text.strip():
            return
        pushed_back = session.awaiting_feedback and bool(PUSH_BACK.search(text))
        after_question = bool(session.messages) and session.messages[-1].role == "assistant" and \
            session.questions_asked > 0 and not session.awaiting_feedback
        choice = re.fullmatch(r"\W*(\d)\W*", text)
        session.picked = ""
        if after_question and choice and 1 <= int(choice.group(1)) <= len(session.options):
            session.picked = session.options[int(choice.group(1)) - 1]  # "2" means the second choice
        offered = session.awaiting_offer
        if TOPIC_CHANGE.match(text):
            # "never mind, I can't log in": a new question, not an answer to the last one.
            after_question, session.options, session.questions_asked, session.picked = False, [], 0, ""
            session.topic_start = len(session.merchant_texts())
        session.messages.append(Message("merchant", text.strip()))
        if offered and YES.fullmatch(text.strip()):
            return self.hand_off(session, "not_covered")
        if offered and NO.fullmatch(text.strip()):
            return self.decline_offer(session, typed=True)

        if ASK_FOR_PERSON.search(text):
            self._triage(session)
            return self.hand_off(session, "asked")
        if pushed_back:
            self._triage(session)
            return self.hand_off(session, "pushed_back")
        if after_question and NONE_OF_THESE.fullmatch(text.strip()):
            # "none of the above": ask once in open words, then hand off. No AI call needed.
            if session.questions_asked < 2:
                session.questions_asked += 1
                session.messages.append(Message("assistant", CLARIFY_FALLBACK))
                return
            self._triage(session)
            session.note_for_agent = "The merchant's problem didn't match the help-center cases offered."
            return self.hand_off(session, "not_covered")
        if session.cost_usd >= self.max_cost:
            return self.hand_off(session, "error")

        if not self._triage(session):
            return self.hand_off(session, "error")
        if session.triage.get("ai_urgency") == "urgent":
            return self.hand_off(session, "urgent")

        try:
            outcome = self.answerer.answer(self._question(session), search_text=self._search_text(session))
        except AnswerError:
            return self.hand_off(session, "error")
        session.cost_usd += outcome.cost_usd
        if not outcome.result.answered:
            session.note_for_agent = outcome.result.missing or outcome.note
            r = outcome.result
            # A short message the AI couldn't place is vague ("cant log in"), unless it names something the help
            # center never mentions ("QuickBooks"): then it's clear, just not covered.
            words = tokens(text)
            unknown = [w for w in words if len(w) >= 5 and w not in self.answerer.search.idf]
            needs_detail = getattr(r, "needs_detail", False) or (len(words) < SHORT_MESSAGE_WORDS and not unknown)
            if needs_detail and session.questions_asked < MAX_CLARIFYING_QUESTIONS:
                # A vague message ("cant log in") gets a question, not a hand-off.
                options = list(getattr(r, "options", []))
                if len(options) < 2 and getattr(outcome, "searched", None):
                    options = cases_from_article(outcome.searched[0], text)  # the AI gave no choices
                question = _drop_greeting(r.reply) if getattr(r, "needs_detail", False) else ""
                session.messages.append(Message("assistant", self._clarifying_question(session, options, question)))
                session.questions_asked += 1
                return
            if needs_detail:  # we asked enough and still couldn't place it: don't claim the articles lack it
                return self.offer_person(session, "I'm sorry I wasn't able to find the right answer for you here.")
            return self.offer_person(session, r.reply)

        reply = _drop_greeting(outcome.result.reply)
        unsupported = unsupported_facts(reply, outcome.sources)
        if unsupported:
            # Never send a fact the articles don't contain: an invented price or menu name is worse than no answer.
            session.note_for_agent = ("Answer held back: it mentioned " + ", ".join(unsupported[:5]) +
                                      ", which the cited articles don't contain.")
            return self.offer_person(session, "I want to make sure I give you accurate information on this.")
        if self._repeats_last_answer(session, reply):
            session.note_for_agent = outcome.result.missing or "The merchant pushed back on the AI's answer."
            return self.hand_off(session, "repeat")
        if outcome.result.missing:
            session.note_for_agent = outcome.result.missing
        session.answers_given += 1
        session.questions_asked, session.options = 0, []  # the next vague question starts a fresh round
        session.messages.append(Message("assistant", format_chat_reply(reply), outcome.sources, answered=True))

    def offer_person(self, session: ChatSession, ai_sentence: str = "") -> None:
        """The articles don't cover it: say so, and ask whether to connect a specialist, as a person would."""
        sentence = _drop_greeting(ai_sentence)
        if not sentence or len(sentence) > 250 or re.search(r"connect|specialist|pass", sentence, re.IGNORECASE):
            sentence = "I'm afraid I don't have the details on that."
        session.messages.append(Message("assistant", f"{sentence} {OFFER_QUESTION}", offer=True))

    def decline_offer(self, session: ChatSession, typed: bool = False) -> None:
        """The merchant doesn't want a specialist (yet): carry on with the chat."""
        if not typed:
            session.messages.append(Message("merchant", "No, thanks"))
        session.messages.append(Message("assistant", "No problem. Is there anything else I can help you with?"))

    def resolve(self, session: ChatSession) -> None:
        """The merchant said the answer solved the problem."""
        if not session.is_open:
            return
        session.status = "resolved"
        session.messages.append(Message("assistant", "I am glad I could help. Thank you for contacting Storely "
                                                     "Support, and have a good day."))
        session.ticket_id = self.tickets.save(session, closed=True, outcome=RESOLVED)

    def hand_off(self, session: ChatSession, reason: str) -> None:
        if not session.is_open:
            return
        session.status = "handed_off"
        session.handoff_reason = HANDOFF_REASONS[reason]
        email = session.merchant.email or "the address on your account"
        session.messages.append(Message("assistant", HANDOFF_MESSAGES[reason].format(email=email)))
        session.ticket_id = self.tickets.save(session, closed=False, outcome=f"{HANDED_OFF}: {session.handoff_reason}")

    def _triage(self, session: ChatSession) -> bool:
        # Only the merchant's own words are triaged. The assistant's replies contain words like "immediately"
        # or "compromised" that would make a calm question look urgent.
        ticket = session.as_ticket()
        ticket.body = "\n\n".join(session.merchant_texts())
        try:
            outcome = self.triager.triage(ticket)
        except TriageError:
            return False
        session.cost_usd += outcome.cost_usd
        session.triage = outcome.as_columns()
        return True

    @staticmethod
    def _clarifying_question(session: ChatSession, options: list[str], question: str = "") -> str:
        """Numbered choices when there are some, so the merchant can just pick one, otherwise an open question.
        The AI writes the question in its own words; the code lays out the choices the same way every time."""
        options = [o.strip().rstrip(".") for o in options if o.strip()][:4]
        options = [o for o in options if not o.lower().startswith("something else")]  # the footer says that
        question = question.strip() if "?" in question and len(question) < 300 else ""
        if len(options) >= 2:
            session.options = options
            lines = "\n".join(f"{i}. {o}" for i, o in enumerate(options, 1))
            return f"{question or CHOICE_QUESTION}\n\n{lines}\n\n{CHOICE_FOOTER}"
        session.options = []
        return question or OPEN_QUESTION

    @staticmethod
    def _repeats_last_answer(session: ChatSession, reply: str) -> bool:
        # Sending the same steps again never helps: it usually means the merchant pushed back on them.
        last = next((m for m in reversed(session.messages) if m.answered), None)
        if not last:
            return False
        body = lambda t: t.split("\n", 1)[-1].lower()  # ignore the opening line, which often changes
        return SequenceMatcher(None, body(last.text), body(format_chat_reply(reply))).ratio() >= REPEAT_SIMILARITY

    def _search_text(self, session: ChatSession) -> str:
        # Search on the latest message. A short follow-up ("and for Canada?") also uses the message before it.
        # Right after a clarifying question, the whole conversation so far is one question.
        texts = session.merchant_texts()[session.topic_start:]  # earlier topics don't help the search
        texts[-1] = TOPIC_CHANGE.sub("", texts[-1]) or texts[-1]
        if ABOUT_STORELY.search(texts[-1]):
            return f"{texts[-1]} what Storely offers services plans"  # "tell me about your products" is about us
        if session.picked:
            texts = texts[:-1] + [session.picked]
        if session.questions_asked and not session.answers_given and len(texts[-1].split()) < 8:
            return " ".join(texts)  # a short answer to our question needs the question it answers
        if len(texts) > 1 and len(texts[-1].split()) < 5:
            return f"{texts[-2]} {texts[-1]}"
        return texts[-1]

    def _question(self, session: ChatSession) -> Ticket:
        # The search and the AI focus on the latest message, with the conversation for context.
        ticket = session.as_ticket()
        ticket.subject = session.merchant_texts()[-1]
        ticket.body = ("Conversation so far:\n\n" + session.transcript() +
                       "\n\nAnswer the merchant's latest message.\n\nAll help-center topics (for choices when the message is "
                       "broad): " + "; ".join(a.title for a in self.answerer.search.articles))
        return ticket


def unsupported_facts(reply: str, sources: list[Article]) -> list[str]:
    """Numbers, prices, percentages and bold names (buttons, menus, forms) in the reply that none of the cited
    articles contains. Anything here may be invented, so the reply is not sent."""
    text = " ".join(f"{a.title} {a.body}" for a in sources).replace("**", "").lower()
    missing = []
    body = re.sub(r"^\s*\d+[.)]\s", "", reply, flags=re.M)  # step numbers ("1. Go to") aren't facts
    for number in re.findall(r"\d[\d,]*(?:\.\d+)?%?", body):
        if number.rstrip(",") not in text:
            missing.append(number)
    for name in re.findall(r"\*\*(.+?)\*\*", reply):
        if name.lower().strip(" .:") not in text:
            missing.append(f"“{name}”")
    return list(dict.fromkeys(missing))


def cases_from_article(article: Article, question: str) -> list[str]:
    """The likely cases from the best article's sections, such as "I forgot my password"."""
    from src.answer.fake_client import likely_cases
    return likely_cases(f'<article id="{article.article_id}" title="{article.title}">\n{article.body}</article>', question)


def _drop_greeting(text: str) -> str:
    # The chat page already says "Hello <name>, welcome", so a reply never greets again.
    text = text.strip()
    first, _, rest = text.partition("\n")
    if re.match(r"^(hello|hi|dear)\b[^.?!\n]{0,40},\s*$", first, re.IGNORECASE) and rest.strip():
        return rest.strip()
    return text


def ticket_columns(session: ChatSession, outcome: str) -> dict:
    """The values saved with a finished chat's ticket, using the same columns as the other tickets."""
    t = session.triage
    last_answer = next((m for m in reversed(session.messages) if m.answered), None)
    columns = {
        **{k: v for k, v in t.items() if v},
        "chat_outcome": outcome,
        "ai_answered": "yes" if session.status == "resolved" else "no",
        "ai_missing": session.note_for_agent or session.handoff_reason,
    }
    if last_answer:
        columns["ai_sources"] = "; ".join(f"{a.article_id} {a.title}" for a in last_answer.sources)
    if session.status == "resolved":
        columns["agent_status"] = RESOLVED
    return columns
