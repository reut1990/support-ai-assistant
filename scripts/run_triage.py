"""Triages tickets and writes the results back to the data source (Google Sheet or local file).

Free practice run, no API key needed:
    python -m scripts.run_triage --fake --limit 10

Real run with Claude. Shows the estimated cost and asks before spending anything:
    python -m scripts.run_triage --limit 10

Options:
    --limit N       how many tickets (default 10)
    --model NAME    claude-haiku-5-5 (default), claude-sonnet-5-5 or claude-opus-5-5
    --max-cost USD  stop the run if actual spending reaches this amount (default 0.50)
    --redo          triage again tickets that already have AI results (skipped by default, so you never pay twice)
    --yes           skip the confirmation question
"""

import argparse
import sys

from src.connectors import get_data_source
from src.triage.cost import estimate_run
from src.triage.engine import DEFAULT_MODEL, Triager, TriageError
from src.triage.fake_client import FakeClaudeClient
from src.triage.prompt import SYSTEM_PROMPT, ticket_message


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Triage support tickets with Claude.")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--max-cost", type=float, default=0.50)
    p.add_argument("--fake", action="store_true", help="use the free keyword-based fake AI")
    p.add_argument("--redo", action="store_true", help="re-triage tickets that already have results")
    p.add_argument("--yes", action="store_true")
    args = p.parse_args(argv)

    source = get_data_source()
    tickets = source.list_tickets()[: args.limit]
    if not args.redo:
        done_before = source.list_triage()
        skipped = [t for t in tickets if t.ticket_id in done_before]
        tickets = [t for t in tickets if t.ticket_id not in done_before]
        if skipped:
            print(f"Skipping {len(skipped)} tickets that already have AI results (use --redo to triage them again).")
    if not tickets:
        print("Nothing left to triage.")
        return 0
    messages = [ticket_message(t.subject, t.body, t.plan, t.channel) for t in tickets]

    if args.fake:
        triager = Triager(client=FakeClaudeClient(), model=args.model)
        print(f"Fake AI: {len(tickets)} tickets, cost $0.00 (no API calls).")
    else:
        estimate = estimate_run(args.model, SYSTEM_PROMPT, messages)
        print(f"About to triage {len(tickets)} tickets with {args.model}.")
        print(f"Estimated cost: ${estimate:.4f}. The run stops if spending reaches ${args.max_cost:.2f}.")
        if not args.yes and input("Continue? Type y and press Enter: ").strip().lower() != "y":
            print("Cancelled. Nothing was charged.")
            return 0
        triager = Triager(model=args.model)

    spent = 0.0
    done = 0
    for ticket in tickets:
        if spent >= args.max_cost:
            print(f"Stopped: spending reached ${spent:.4f}, the --max-cost limit.")
            break
        try:
            outcome = triager.triage(ticket)
        except TriageError as e:
            print(f"Skipped {e}")
            continue
        spent += outcome.cost_usd
        source.write_triage(ticket.ticket_id, outcome.as_columns())
        done += 1
        r = outcome.result
        print(f"{ticket.ticket_id}  {r.category:9} {r.urgency:7} {r.sentiment:10} churn:{r.churn_risk:6} -> {outcome.queue}")

    cost_note = "$0.00 (fake AI)" if args.fake else f"${spent:.4f}"
    print(f"\nTriaged {done} tickets and wrote results to: {source.name}. Actual cost: {cost_note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
