"""Drafts replies to tickets from the help articles and writes them back to the data source.

Free practice run, no API key needed:
    python -m scripts.run_answers --fake --limit 10

Real run with Claude. Shows the estimated cost and asks before spending anything:
    python -m scripts.run_answers --limit 10

See one full reply:
    python -m scripts.run_answers --ticket T-1001

Options:
    --limit N       how many tickets (default 10)
    --ticket ID     draft a reply for one ticket and print it in full
    --model NAME    claude-haiku-5-5 (default), claude-sonnet-5-5 or claude-opus-5-5
    --max-cost USD  stop the run if actual spending reaches this amount (default 0.50)
    --redo          draft again for tickets that already have a reply (skipped by default, so you never pay twice)
    --yes           skip the confirmation question
"""

import argparse
import sys

from src.answer.engine import Answerer, AnswerError
from src.answer.fake_client import FakeAnswerClient
from src.answer.prompt import SYSTEM_PROMPT
from src.connectors import get_data_source
from src.triage.cost import EXPECTED_REPLY_TOKENS, estimate_run
from src.triage.engine import DEFAULT_MODEL


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Draft replies to support tickets from the help articles.")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--ticket")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--max-cost", type=float, default=0.50)
    p.add_argument("--fake", action="store_true", help="use the free template-based fake AI")
    p.add_argument("--redo", action="store_true", help="draft again for tickets that already have a reply")
    p.add_argument("--yes", action="store_true")
    args = p.parse_args(argv)

    source = get_data_source()
    tickets = source.list_tickets()
    if args.ticket:
        tickets = [t for t in tickets if t.ticket_id == args.ticket]
        if not tickets:
            print(f"Ticket {args.ticket} not found.")
            return 1
    else:
        tickets = tickets[: args.limit]
        if not args.redo:
            done_before = source.list_replies()
            skipped = [t for t in tickets if t.ticket_id in done_before]
            tickets = [t for t in tickets if t.ticket_id not in done_before]
            if skipped:
                print(f"Skipping {len(skipped)} tickets that already have a reply (use --redo to draft them again).")
    if not tickets:
        print("Nothing left to answer.")
        return 0

    articles = source.list_articles()
    if args.fake:
        answerer = Answerer(articles, client=FakeAnswerClient(), model=args.model)
        print(f"Fake AI: {len(tickets)} ticket{'s' if len(tickets) != 1 else ''}, cost $0.00 (no API calls).")
    else:
        # A placeholder client: this answerer only builds the messages for the estimate, so no key is needed yet.
        answerer = Answerer(articles, client=object(), model=args.model)
        messages = [answerer.message_for(t) for t in tickets]
        estimate = estimate_run(args.model, SYSTEM_PROMPT, messages, EXPECTED_REPLY_TOKENS)
        print(f"About to draft replies for {len(tickets)} tickets with {args.model}.")
        print(f"Estimated cost: ${estimate:.4f}. The run stops if spending reaches ${args.max_cost:.2f}.")
        if not args.yes and input("Continue? Type y and press Enter: ").strip().lower() != "y":
            print("Cancelled. Nothing was charged.")
            return 0
        answerer = Answerer(articles, model=args.model)

    spent = 0.0
    done = handed_off = 0
    for ticket in tickets:
        if spent >= args.max_cost:
            print(f"Stopped: spending reached ${spent:.4f}, the --max-cost limit.")
            break
        try:
            outcome = answerer.answer(ticket)
        except AnswerError as e:
            print(f"Skipped {e}")
            continue
        spent += outcome.cost_usd
        source.write_reply(ticket.ticket_id, outcome.as_columns())
        done += 1
        cols = outcome.as_columns()
        if outcome.result.answered:
            print(f"{ticket.ticket_id}  answered   from {', '.join(a.article_id for a in outcome.sources)}")
        else:
            handed_off += 1
            print(f"{ticket.ticket_id}  I don't know -> hand to a person: {cols['ai_missing']}")
        if args.ticket:
            print(f"\nSubject: {ticket.subject}\n{ticket.body}\n\n--- Draft reply ---\n{cols['ai_reply']}")
            if cols["ai_sources"]:
                print(f"\nSources: {cols['ai_sources']}")

    cost_note = "$0.00 (fake AI)" if args.fake else f"${spent:.4f}"
    print(f"\nDrafted {done} {'reply' if done == 1 else 'replies'} ({handed_off} handed to a person) and wrote them to: {source.name}. "
          f"Actual cost: {cost_note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
