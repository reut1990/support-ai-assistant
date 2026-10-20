"""A stand-in for the Claude API that answers with simple keyword rules.

It costs nothing and needs no API key, so the whole app can be tried and tested for free.
Its answers are much less accurate than the real AI.
"""

from types import SimpleNamespace

from src.triage.schema import TriageResult

KEYWORDS = [
    ("account", ["hack", "log in", "login", "2fa", "two-step", "password", "staff", "suspend", "ownership"]),
    ("payments", ["payout", "chargeback", "verification", "apple pay", "refund", "storely payments"]),
    ("domains", ["domain", "dns", "ssl", "not secure", "www", "site can't", "down"]),
    ("checkout", ["checkout", "discount", "tax", "abandon"]),
    ("shipping", ["shipping", "label", "pickup", "tracking", "customs", "delivery"]),
    ("apps", ["app", "api", "integration", "sync", "quickbooks", "instagram"]),
    ("themes", ["theme", "font", "image", "mobile", "footer", "css", "slow"]),
    ("billing", ["charged", "invoice", "plan", "bill", "subscription", "fee", "cancel"]),
    ("orders", ["order", "inventory", "product", "variant", "fraud"]),
]


def fake_triage(text: str) -> TriageResult:
    t = text.lower()
    category = next((c for c, words in KEYWORDS if any(w in t for w in words)), "orders")
    angry = any(w in t for w in ["unacceptable", "now", "!!", "furious", "disaster", "third time"]) or "??" in t
    upset = angry or any(w in t for w in ["still", "not working", "broken", "wrong", "can't", "why"])
    urgent = any(w in t for w in ["right now", "immediately", "hacked", "down", "can't capture", "0 products"])
    leaving = any(w in t for w in ["another platform", "elsewhere", "disputing", "refund me"])
    return TriageResult(
        category=category,
        urgency="urgent" if urgent else "high" if angry else "medium" if upset else "low",
        sentiment="angry" if angry else "frustrated" if upset else "neutral",
        churn_risk="high" if leaving or angry else "medium" if upset else "low",
        reason="Keyword-based guess from the fake AI (no API call).",
    )


class FakeClaudeClient:
    """Implements the one method the triage engine uses: client.messages.parse(...)."""

    def __init__(self):
        self.messages = self
        self.calls = 0

    def parse(self, *, messages, system, **kwargs):
        self.calls += 1
        text = messages[-1]["content"]
        return SimpleNamespace(
            parsed_output=fake_triage(text),
            stop_reason="end_turn",
            usage=SimpleNamespace(input_tokens=(len(system) + len(text)) // 4, output_tokens=120),
        )
