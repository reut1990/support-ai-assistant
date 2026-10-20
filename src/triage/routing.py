"""Business rules that turn a triage result into a queue.

Routing is plain code, not AI, so a support manager can read and change the rules.
"""

QUEUES = {
    "billing": "Billing",
    "payments": "Payments",
    "domains": "Technical",
    "checkout": "Technical",
    "apps": "Technical",
    "themes": "Store Setup",
    "shipping": "Store Setup",
    "orders": "Store Setup",
    "account": "Account Security",
}
ESCALATIONS = "Priority Escalations"


def route(category: str, urgency: str, sentiment: str, churn_risk: str) -> str:
    # Urgent tickets, and angry merchants likely to leave, skip the normal queue.
    if urgency == "urgent" or (churn_risk == "high" and sentiment == "angry"):
        return ESCALATIONS
    return QUEUES.get(category, "General")
