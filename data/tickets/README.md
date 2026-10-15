# Sample tickets

`tickets.csv` holds 100 support tickets from merchants on **Storely**, a fictional Shopify-style store builder. Every ticket, merchant and email address is made up.

`build_tickets.py` generates the CSV from the hand-written tickets inside it. Run `python data/tickets/build_tickets.py` to rebuild it.

## Columns

| Column | Meaning |
| --- | --- |
| `ticket_id`, `created_at`, `channel` | Ticket metadata |
| `customer_name`, `customer_email`, `store_name`, `plan` | Fictional merchant details |
| `subject`, `body` | What the merchant wrote |
| `label_category` | billing, payments, domains, checkout, themes, apps, shipping, account, orders |
| `label_urgency` | low, medium, high, urgent |
| `label_sentiment` | positive, neutral, frustrated, angry |
| `label_churn_risk` | low, medium, high |

The `label_*` columns are the correct answers written by a person. The AI never sees them; they are used only to measure its accuracy.

## Label counts

- **Category:** 11 tickets each, except orders with 12
- **Urgency:** 34 low, 40 medium, 20 high, 6 urgent
- **Sentiment:** 10 positive, 43 neutral, 33 frustrated, 14 angry
- **Churn risk:** 59 low, 27 medium, 14 high
