from evaluation.evaluate import build_report, compare
from src.models import Ticket


def ticket(tid, cat, urg, sent, churn):
    return Ticket(tid, "", "", "", "", "", "", f"Subject {tid}", "",
                  labels={"category": cat, "urgency": urg, "sentiment": sent, "churn_risk": churn})


def ai(cat, urg, sent, churn, queue):
    return {"ai_category": cat, "ai_urgency": urg, "ai_sentiment": sent, "ai_churn_risk": churn,
            "ai_queue": queue, "ai_reason": "because"}


def test_compare_scores_and_escalations():
    tickets = [
        ticket("T-1", "payments", "urgent", "angry", "high"),   # needs escalation
        ticket("T-2", "billing", "low", "neutral", "low"),
        ticket("T-3", "domains", "medium", "frustrated", "medium"),
        ticket("T-4", "orders", "low", "neutral", "low"),        # not triaged yet
    ]
    triage = {
        "T-1": ai("payments", "urgent", "angry", "high", "Priority Escalations"),
        "T-2": ai("billing", "medium", "neutral", "low", "Billing"),        # urgency one level off
        "T-3": ai("checkout", "urgent", "frustrated", "medium", "Priority Escalations"),  # wrong + extra flag
    }
    s = compare(tickets, triage)
    assert s["n"] == 3
    assert s["fields"]["category"]["exact"] == 2
    assert s["fields"]["urgency"]["exact"] == 1
    assert s["fields"]["urgency"]["within_one"] == 2
    e = s["escalations"]
    assert (e["should"], e["caught"], len(e["extra"])) == (1, 1, 1)
    report = build_report(s)
    assert "| T-3 | Subject T-3 | category | domains | checkout | because |" in report
    assert "caught **1 of 1**" in report
