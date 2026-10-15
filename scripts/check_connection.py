"""Checks that the app can read tickets and articles from the configured data source.

Run from the project folder:  python -m scripts.check_connection
Use DATA_SOURCE=google (or local) in .env to choose what to check.
"""

from src.connectors import get_data_source


def main() -> None:
    source = get_data_source()
    tickets = source.list_tickets()
    articles = source.list_articles()
    print(f"Data source: {source.name}")
    print(f"Tickets:  {len(tickets)}  (first: {tickets[0].ticket_id} '{tickets[0].subject}')" if tickets else "Tickets:  0")
    print(f"Articles: {len(articles)}  (first: {articles[0].article_id} '{articles[0].title}')" if articles else "Articles: 0")
    print("Connection OK" if tickets and articles else "Connected, but something is missing. Check the setup guide.")


if __name__ == "__main__":
    main()
