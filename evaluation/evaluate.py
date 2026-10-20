"""Compares the AI's saved triage results with the correct labels and writes an accuracy report.

This makes no API calls and costs nothing. Run it after scripts.run_triage:
    python -m evaluation.evaluate

It prints a summary and writes evaluation/report.md.
"""

from collections import Counter
from pathlib import Path

from src.connectors import get_data_source
from src.triage.prompt import PROMPT_VERSION
from src.triage.routing import ESCALATIONS, route

FIELDS = ["category", "urgency", "sentiment", "churn_risk"]
# Fields with an order, where being one step off is a near miss rather than a full miss.
SCALES = {
    "urgency": ["low", "medium", "high", "urgent"],
    "sentiment": ["positive", "neutral", "frustrated", "angry"],
    "churn_risk": ["low", "medium", "high"],
}
REPORT = Path(__file__).with_name("report.md")


def compare(tickets, triage: dict[str, dict]) -> dict:
    rows = []
    for t in tickets:
        ai = triage.get(t.ticket_id)
        if not ai or not t.labels:
            continue
        rows.append({
            "ticket": t,
            "ai": {f: ai[f"ai_{f}"] for f in FIELDS},
            "label": {f: t.labels.get(f, "") for f in FIELDS},
            "ai_queue": ai.get("ai_queue", ""),
            "reason": ai.get("ai_reason", ""),
        })
    stats = {"n": len(rows), "rows": rows, "fields": {}}
    for f in FIELDS:
        exact = sum(r["ai"][f] == r["label"][f] for r in rows)
        within_one = None
        if f in SCALES:
            idx = SCALES[f].index
            within_one = sum(abs(idx(r["ai"][f]) - idx(r["label"][f])) <= 1 for r in rows)
        misses = Counter((r["label"][f], r["ai"][f]) for r in rows if r["ai"][f] != r["label"][f])
        stats["fields"][f] = {"exact": exact, "within_one": within_one, "misses": misses}

    # Escalations: did the AI send the tickets that needed escalating to Priority Escalations?
    should = [r for r in rows if route(*(r["label"][f] for f in FIELDS)) == ESCALATIONS]
    did = [r for r in rows if r["ai_queue"] == ESCALATIONS]
    caught = [r for r in should if r["ai_queue"] == ESCALATIONS]
    stats["escalations"] = {"should": len(should), "flagged": len(did), "caught": len(caught),
                            "missed": [r for r in should if r["ai_queue"] != ESCALATIONS],
                            "extra": [r for r in did if r not in should]}
    return stats


def pct(a: int, b: int) -> str:
    return f"{100 * a / b:.0f}%" if b else "n/a"


def build_report(stats: dict) -> str:
    n = stats["n"]
    lines = [f"# Triage accuracy report: version {PROMPT_VERSION.removeprefix('v')} instructions", "",
             f"The AI's answers for **{n} tickets** compared with labels written by a person.", "",
             "| Field | Exactly right | Right or one level off |", "| --- | --- | --- |"]
    for f, s in stats["fields"].items():
        near = pct(s["within_one"], n) if s["within_one"] is not None else "n/a"
        lines.append(f"| {f.replace('_', ' ').capitalize()} | {pct(s['exact'], n)} ({s['exact']}/{n}) | {near} |")
    e = stats["escalations"]
    lines += ["", "## Escalations", "",
              f"Tickets that needed **Priority Escalations** (urgent, or angry with high churn risk): **{e['should']}**.",
              f"The AI caught **{e['caught']} of {e['should']}** ({pct(e['caught'], e['should'])}) "
              f"and flagged {len(e['extra'])} extra ticket(s) that didn't need it.", ""]
    for r in e["missed"]:
        t = r["ticket"]
        lines.append(f"- Missed: {t.ticket_id} \"{t.subject}\" went to {r['ai_queue'] or 'no queue'}")
    lines += ["", "## Most common mistakes", ""]
    for f, s in stats["fields"].items():
        if s["misses"]:
            top = ", ".join(f"{label} → {ai} ({k}×)" for (label, ai), k in s["misses"].most_common(4))
            lines.append(f"- **{f.replace('_', ' ').capitalize()}** (correct → AI): {top}")
    lines += ["", "## Every mistake", "", "| Ticket | Subject | Field | Correct | AI | AI's reason |",
              "| --- | --- | --- | --- | --- | --- |"]
    for r in stats["rows"]:
        for f in FIELDS:
            if r["ai"][f] != r["label"][f]:
                t = r["ticket"]
                reason = r["reason"].replace("|", "/")
                lines.append(f"| {t.ticket_id} | {t.subject} | {f} | {r['label'][f]} | {r['ai'][f]} | {reason} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    source = get_data_source()
    stats = compare(source.list_tickets(), source.list_triage())
    if not stats["n"]:
        print("No triage results found yet. Run: python -m scripts.run_triage --limit 100")
        return
    REPORT.write_text(build_report(stats), encoding="utf-8")
    print(f"Compared {stats['n']} tickets from: {source.name}\n")
    for f, s in stats["fields"].items():
        near = f"   right or one level off: {pct(s['within_one'], stats['n'])}" if s["within_one"] is not None else ""
        print(f"{f:11} exactly right: {pct(s['exact'], stats['n']):>4}{near}")
    e = stats["escalations"]
    print(f"\nEscalations caught: {e['caught']} of {e['should']}, extra flagged: {len(e['extra'])}")
    print(f"\nFull report with every mistake: {REPORT}")


if __name__ == "__main__":
    main()
