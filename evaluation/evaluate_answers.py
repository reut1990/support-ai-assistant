"""Checks the drafted replies and writes a report. Makes no API calls and costs nothing.

Run it after scripts.run_answers:
    python -m evaluation.evaluate_answers

What it measures:
- "I don't know": tickets about topics with no help article should be handed to a person, not answered.
- Answered: how many of the other tickets got a reply based on an article.
- Right source: whether the cited article belongs to the ticket's correct category (labeled by a person).
It also lists sample replies, because whether a reply reads well still needs a person to judge.
"""

from pathlib import Path

from src.answer.prompt import PROMPT_VERSION
from src.connectors import get_data_source

# Tickets about topics the help center deliberately doesn't cover (see data/help_articles/README.md).
NOT_COVERED = {
    "T-1057": "QuickBooks",
    "T-1062": "Instagram",
    "T-1077": "delivery date",
    "T-1088": "suspension appeal",
    "T-1095": "pre-orders",
}
REPORT = Path(__file__).with_name("answers_report.md")
SAMPLES = 5


def compare(tickets, replies: dict[str, dict], articles) -> dict:
    category_of = {a.article_id: a.category for a in articles}
    rows = []
    for t in tickets:
        r = replies.get(t.ticket_id)
        if not r:
            continue
        cited = [s.split(" ", 1)[0] for s in r["ai_sources"].split("; ") if s]
        rows.append({"ticket": t, "answered": r["ai_answered"] == "yes", "reply": r["ai_reply"],
                     "cited": cited, "missing": r["ai_missing"],
                     "right_source": any(category_of.get(c) == t.labels.get("category") for c in cited)})
    gaps = [r for r in rows if r["ticket"].ticket_id in NOT_COVERED]
    covered = [r for r in rows if r["ticket"].ticket_id not in NOT_COVERED]
    answered = [r for r in covered if r["answered"]]
    return {
        "n": len(rows),
        "gaps": gaps,
        "gaps_handed_off": [r for r in gaps if not r["answered"]],
        "gaps_answered": [r for r in gaps if r["answered"]],
        "covered": covered,
        "answered": answered,
        "handed_off": [r for r in covered if not r["answered"]],
        "right_source": [r for r in answered if r["right_source"]],
        "other_source": [r for r in answered if not r["right_source"]],
    }


def pct(a: int, b: int) -> str:
    return f"{100 * a / b:.0f}%" if b else "n/a"


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def build_report(s: dict) -> str:
    lines = [
        f"# Reply drafting report: version {PROMPT_VERSION.removeprefix('v')} instructions",
        "",
        f"Replies drafted from the help articles for **{s['n']} tickets**.",
        "",
        "| Check | Result |",
        "| --- | --- |",
        f"| Said \"I don't know\" when no article covers the topic | {len(s['gaps_handed_off'])} of {len(s['gaps'])} |",
        f"| Answered tickets that an article covers | {len(s['answered'])} of {len(s['covered'])} "
        f"({pct(len(s['answered']), len(s['covered']))}) |",
        f"| Answers citing an article from the ticket's correct category | {len(s['right_source'])} of "
        f"{len(s['answered'])} ({pct(len(s['right_source']), len(s['answered']))}) |",
        "",
    ]
    if s["gaps_answered"]:
        lines += ["## Answered when it should have said \"I don't know\"", ""]
        lines += [f"- {r['ticket'].ticket_id} \"{r['ticket'].subject}\" ({NOT_COVERED[r['ticket'].ticket_id]})"
                  for r in s["gaps_answered"]]
        lines.append("")
    if s["handed_off"]:
        lines += ["## Handed to a person although an article may cover it", "",
                  "| Ticket | Subject | What the AI said was missing |", "| --- | --- | --- |"]
        lines += [f"| {r['ticket'].ticket_id} | {_cell(r['ticket'].subject)} | {_cell(r['missing'])} |"
                  for r in s["handed_off"]]
        lines.append("")
    if s["other_source"]:
        lines += ["## Answers citing an article from another category", "",
                  "Not always wrong: a ticket labeled *apps* can be answered by the orders article, for example.", "",
                  "| Ticket | Subject | Correct category | Cited |", "| --- | --- | --- | --- |"]
        lines += [f"| {r['ticket'].ticket_id} | {_cell(r['ticket'].subject)} | {r['ticket'].labels.get('category', '')} "
                  f"| {', '.join(r['cited'])} |" for r in s["other_source"]]
        lines.append("")
    lines += ["## Sample replies", ""]
    samples = s["answered"][:SAMPLES] + s["gaps"][:2]
    for r in samples:
        t = r["ticket"]
        source = f"Sources: {', '.join(r['cited'])}" if r["cited"] else "Handed to a person"
        lines += [f"### {t.ticket_id}: {t.subject}", "", f"> {t.body}", "", r["reply"], "", f"*{source}*", ""]
    return "\n".join(lines)


def main() -> int:
    source = get_data_source()
    tickets = source.list_tickets()
    replies = source.list_replies()
    if not replies:
        print("No drafted replies found. Run: python -m scripts.run_answers")
        return 1
    s = compare(tickets, replies, source.list_articles())
    REPORT.write_text(build_report(s), encoding="utf-8")
    print(f"Checked {s['n']} drafted replies from: {source.name}\n")
    print(f"Said \"I don't know\" on uncovered topics: {len(s['gaps_handed_off'])} of {len(s['gaps'])}")
    print(f"Answered covered tickets:               {len(s['answered'])} of {len(s['covered'])}")
    print(f"Cited an article from the right category: {pct(len(s['right_source']), len(s['answered']))}")
    print(f"\nFull report with sample replies: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
