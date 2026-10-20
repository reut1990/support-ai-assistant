# Support AI Assistant

An AI assistant for a customer support team at a Shopify-style ecommerce store builder.

It triages incoming merchant tickets (category, urgency, sentiment, churn risk), drafts replies from the help center for human agents, and runs a customer-facing chat agent that hands off to a human with a summary when it should.

> 🚧 Work in progress. This README will be rewritten when the project is complete.

## Planned features

1. **Triage engine:** tags each ticket and routes it to the right queue.
2. **Help-center answers:** answers only from the help articles and cites them.
3. **Agent assist:** a screen showing triage results and an editable draft reply.
4. **Support chat agent:** answers customers directly and hands off to a human when needed.
5. **Integrations:** Freshdesk and Google Drive (Sheets and Docs), with local sample data as a fallback.
6. **Evaluation:** triage accuracy measured against labeled sample tickets.

## Project layout

```
data/
  tickets/          sample merchant tickets with correct labels
  help_articles/    help-center articles written for this project
src/
  triage/           ticket classification
  knowledge/        answering from help articles
  connectors/       Freshdesk, Google Drive and local-file data sources
app/                web screens (agent assist and chat)
evaluation/         accuracy tests and results
docs/screenshots/   images for this README
```

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env
python -m scripts.check_connection   # reads the sample data in this repository
python -m pytest                     # runs the tests
python -m scripts.run_triage --fake  # free practice triage with a keyword-based fake AI
```

### Triage with Claude

Add your `ANTHROPIC_API_KEY` to `.env`, then:

```bash
python -m scripts.run_triage --limit 10
```

It prints the estimated cost and asks before making any API call. A `--max-cost` limit (default $0.50) stops the run if spending reaches it. With Claude Haiku 5.5, 10 tickets cost well under one cent.

The AI returns each ticket's category, urgency, sentiment and churn risk, using a fixed schema so every answer is valid. Plain business rules in `src/triage/routing.py` then pick the queue, and urgent tickets or angry merchants at risk of leaving go to **Priority Escalations**. Results are written next to each ticket in the Google Sheet, or to `data/output/triage_results.csv` locally.

### Measure accuracy

```bash
python -m scripts.run_triage --limit 100
python -m evaluation.evaluate
```

The second command is free: it compares the saved AI answers with the labels and writes [evaluation/report.md](evaluation/report.md), with scores per field, how many escalations were caught, and every mistake. For comparison, the free keyword-based fake AI (`--fake`) scores 62% on category and 51% on urgency.

To read tickets and articles from Google Drive instead, follow [docs/setup-google-drive.md](docs/setup-google-drive.md).

## Data and credits

All tickets, customers and companies are fictional. Help-article topics are inspired by common questions in the public [Shopify Help Center](https://help.shopify.com), but every article is written from scratch for this project.
