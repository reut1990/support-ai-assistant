"""Loads the sample tickets into HubSpot, one time. Free: it only uses HubSpot's API, never the AI.

    python -m scripts.load_tickets_to_hubspot

What it does:
1. Adds a "Storely AI" group of ticket properties in HubSpot (ticket details and the AI's results).
2. Creates one contact per merchant, so each ticket shows who sent it.
3. Creates the tickets that aren't in HubSpot yet, in the "New" stage of the support pipeline.
4. Copies the AI results you already have (from Google Sheets or the local files) onto the tickets,
   so you don't pay to run the AI again. Use --without-results to skip this.

Running it again is safe: tickets already in HubSpot are skipped.
"""

import argparse
import sys

from src.connectors.hubspot import (HubSpotClient, HubSpotSource, backup_source, create_properties, create_tickets,
                                    upsert_contacts)
from src.models import ALL_RESULT_COLUMNS


def main(argv=None, client=None, source=None) -> int:
    p = argparse.ArgumentParser(description="Load the sample tickets into HubSpot.")
    p.add_argument("--without-results", action="store_true", help="don't copy saved AI results")
    args = p.parse_args(argv)

    client = client or HubSpotClient()
    source = source or backup_source()
    tickets = source.list_tickets()
    print(f"Read {len(tickets)} tickets from: {source.name}")

    created = create_properties(client)
    print(f"Ticket properties ready ({created} new).")

    already = set(HubSpotSource(client=client, articles_source=source, labels_source=source)._all_ids())
    new = [t for t in tickets if t.ticket_id not in already]
    if already:
        print(f"Skipping {len(tickets) - len(new)} tickets already in HubSpot.")
    if not new:
        print("Nothing to load.")
        return 0

    contacts = upsert_contacts(client, new)
    print(f"Contacts ready: {len(contacts)} merchants.")
    results = {} if args.without_results else source.list_results(ALL_RESULT_COLUMNS)
    count = create_tickets(client, new, contacts, results)
    with_results = sum(1 for t in new if t.ticket_id in results)
    print(f"Created {count} tickets in HubSpot ({with_results} with AI results copied). Cost: $0.00")
    return 0


if __name__ == "__main__":
    sys.exit(main())
