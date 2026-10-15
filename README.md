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

## Data and credits

All tickets, customers and companies are fictional. Help-article topics are inspired by common questions in the public [Shopify Help Center](https://help.shopify.com), but every article is written from scratch for this project.
