# Triage accuracy report

The AI's answers for **100 tickets** compared with labels written by a person.

| Field | Exactly right | Right or one level off |
| --- | --- | --- |
| Category | 99% (99/100) | n/a |
| Urgency | 66% (66/100) | 100% |
| Sentiment | 69% (69/100) | 100% |
| Churn risk | 80% (80/100) | 100% |

## Escalations

Tickets that needed **Priority Escalations** (urgent, or angry with high churn risk): **12**.
The AI caught **9 of 12** (75%) and flagged 2 extra ticket(s) that didn't need it.

- Missed: T-1060 "App deleted my products" went to Technical
- Missed: T-1042 "Lost orders because of checkout bug" went to Technical
- Missed: T-1010 "Transaction fees are killing me" went to Billing

## Most common mistakes

- **Category** (correct → AI): account → orders (1×)
- **Urgency** (correct → AI): medium → low (23×), medium → high (4×), high → medium (4×), high → urgent (3×)
- **Sentiment** (correct → AI): frustrated → neutral (17×), angry → frustrated (8×), positive → neutral (5×), neutral → frustrated (1×)
- **Churn risk** (correct → AI): medium → low (13×), high → medium (7×)

## Every mistake

| Ticket | Subject | Field | Correct | AI | AI's reason |
| --- | --- | --- | --- | --- | --- |
| T-1073 | Wrong shipping label address | sentiment | angry | frustrated | Twelve shipping labels printed with the wrong return address and packages are already shipped, so an active problem is costing the merchant and they are requesting a refund. |
| T-1063 | Inventory not syncing with Amazon | urgency | medium | high | The Amazon integration app has stopped syncing inventory, causing overselling of items, which is an active problem costing sales today. |
| T-1087 | Export customer list | urgency | medium | low | This is a neutral how-to question about exporting customer data, with no active problem or churn signals; the closest category is account, though it could arguably fit orders since it concerns customer records. |
| T-1067 | Set up free shipping over $50 | urgency | medium | low | This is a how-to question about configuring shipping rates by order amount, with no active problem or urgency. |
| T-1082 | Change store email | category | account | orders | A neutral how-to question about changing the customer-facing email on order confirmations, with no active problem. |
| T-1040 | Guest checkout | urgency | medium | low | This is a how-to question about enabling guest checkout settings, with no active outage or money at risk. |
| T-1081 | Transfer store ownership | urgency | medium | low | The merchant is asking a how-to question about transferring store ownership, which falls under account management with no active problem. |
| T-1081 | Transfer store ownership | churn_risk | medium | low | The merchant is asking a how-to question about transferring store ownership, which falls under account management with no active problem. |
| T-1070 | Local pickup option | sentiment | frustrated | neutral | Local pickup set up in settings is not showing at checkout, which is a confusing issue with a likely workaround and no sign of lost sales or churn. |
| T-1049 | Edit footer text | urgency | medium | low | A how-to question about editing footer text in the theme, with no urgency or money impact. |
| T-1083 | Locked out after password reset | churn_risk | medium | low | Merchant is locked out of their account after a password reset and has orders to fulfill today, so this is a same-day blocker, though not clearly a compromise. |
| T-1001 | Charged twice this month | sentiment | frustrated | neutral | Merchant was charged twice for their Advanced subscription and asks for the duplicate refund, a time-sensitive but workable billing issue. |
| T-1086 | Multiple stores one login | sentiment | positive | neutral | The merchant asks a how-to question about managing two stores under one login, which is a low-urgency account question with no problem reported. |
| T-1007 | Store paused because payment failed | urgency | high | urgent | Store is frozen after a failed subscription payment so customers cannot buy, and the merchant is actively losing sales despite updating the card. |
| T-1007 | Store paused because payment failed | churn_risk | high | medium | Store is frozen after a failed subscription payment so customers cannot buy, and the merchant is actively losing sales despite updating the card. |
| T-1011 | Pause store while I travel | churn_risk | medium | low | The merchant is asking neutrally about a cheaper plan to keep the store online while closed for orders, which is a plan-change question with no active problem. |
| T-1095 | Pre-orders | urgency | medium | low | This is a neutral how-to question about taking pre-orders for an upcoming product, with no active problem. |
| T-1092 | Order notifications not arriving | sentiment | frustrated | neutral | Merchant is not receiving new order email notifications, which is confusing and disruptive but has a workaround such as checking the dashboard directly. |
| T-1079 | Not receiving 2FA code | urgency | medium | high | Merchant is locked out of their account after changing carriers, blocking their work today, though the problem is not hostile or costing money yet. |
| T-1020 | Refund stuck in pending | urgency | high | medium | A customer refund has been pending for 9 days, causing repeated customer contact, but there is no sign the store is blocked or losing money now. |
| T-1020 | Refund stuck in pending | sentiment | neutral | frustrated | A customer refund has been pending for 9 days, causing repeated customer contact, but there is no sign the store is blocked or losing money now. |
| T-1025 | SSL certificate not working | urgency | high | medium | SSL is not yet active on a domain connected three days ago, causing a 'not secure' warning for customers, which is a broken item with a likely wait-or-check workaround. |
| T-1025 | SSL certificate not working | sentiment | frustrated | neutral | SSL is not yet active on a domain connected three days ago, causing a 'not secure' warning for customers, which is a broken item with a likely wait-or-check workaround. |
| T-1025 | SSL certificate not working | churn_risk | medium | low | SSL is not yet active on a domain connected three days ago, causing a 'not secure' warning for customers, which is a broken item with a likely wait-or-check workaround. |
| T-1032 | Subdomain for wholesale | sentiment | positive | neutral | The merchant asks a how-to question about setting up a subdomain for a separate wholesale storefront, with no active problem. |
| T-1061 | API access for my developer | urgency | medium | low | A neutral how-to question about creating API credentials for a developer's custom warehouse integration, with no blocking issue. |
| T-1096 | Sales report by product | sentiment | positive | neutral | The merchant is asking where to find a product sales report, a how-to question with no active problem, which falls under order reports. |
| T-1065 | Translation app conflicts with theme | urgency | medium | low | Merchant asks who to contact about a translation app causing a menu display conflict, a non-urgent issue with a clear workaround. |
| T-1065 | Translation app conflicts with theme | sentiment | frustrated | neutral | Merchant asks who to contact about a translation app causing a menu display conflict, a non-urgent issue with a clear workaround. |
| T-1035 | Add a tip option at checkout | urgency | medium | low | A neutral how-to question about adding a tip option at checkout, with no active problem. |
| T-1021 | Payment fees higher than expected | urgency | medium | low | The merchant is asking for a breakdown of fees taken from a payout, a question about payments with no blocked money or outage. |
| T-1021 | Payment fees higher than expected | sentiment | frustrated | neutral | The merchant is asking for a breakdown of fees taken from a payout, a question about payments with no blocked money or outage. |
| T-1050 | Mobile layout is broken | urgency | medium | high | A broken mobile layout hides the add to cart button on product pages, which is actively costing sales for a store where most traffic is mobile. |
| T-1015 | Customer chargeback, what do I do? | urgency | high | medium | A merchant asks how to submit chargeback evidence and the deadline, which is time-sensitive but has a clear workaround and no sign of frustration. |
| T-1015 | Customer chargeback, what do I do? | sentiment | frustrated | neutral | A merchant asks how to submit chargeback evidence and the deadline, which is time-sensitive but has a clear workaround and no sign of frustration. |
| T-1015 | Customer chargeback, what do I do? | churn_risk | medium | low | A merchant asks how to submit chargeback evidence and the deadline, which is time-sensitive but has a clear workaround and no sign of frustration. |
| T-1072 | Calculated carrier rates | urgency | medium | low | The merchant is asking a how-to question about showing live UPS carrier rates at checkout instead of flat rates, with no active problem. |
| T-1029 | Transfer domain to Storely | urgency | medium | low | Merchant is asking how-to and fee questions about transferring a domain from Namecheap to Storely, with no active problem. |
| T-1047 | Theme update broke my store | urgency | high | medium | A theme update broke the homepage sections and menu, but the merchant is asking how to roll back, so there is a workaround and the store is still operating. |
| T-1047 | Theme update broke my store | churn_risk | medium | low | A theme update broke the homepage sections and menu, but the merchant is asking how to roll back, so there is a workaround and the store is still operating. |
| T-1041 | Express checkout buttons | sentiment | positive | neutral | A how-to question about adding an express checkout button, with no active problem or urgency. |
| T-1075 | Tracking numbers not sent to customers | urgency | medium | high | Tracking emails aren't reaching customers after fulfillment, causing repeated customer inquiries about orders, which is an active problem blocking daily work but has a possible manual workaround. |
| T-1085 | Staff member can't log in | sentiment | frustrated | neutral | A staff invitation link has expired, blocking one employee from logging in, but a new invitation can be sent as a workaround. |
| T-1097 | Duplicate orders from one customer | sentiment | frustrated | neutral | Merchant asks how to cancel a duplicate order and refund it, a time-sensitive but workable question with no store outage or compromise. |
| T-1097 | Duplicate orders from one customer | churn_risk | medium | low | Merchant asks how to cancel a duplicate order and refund it, a time-sensitive but workable question with no store outage or compromise. |
| T-1100 | All my products disappeared | sentiment | angry | frustrated | All 180 products vanished with no merchant action, so the store cannot sell now and the cause may be a bug or unauthorized access, which fits orders (products/inventory) but needs immediate investigation. |
| T-1100 | All my products disappeared | churn_risk | high | medium | All 180 products vanished with no merchant action, so the store cannot sell now and the cause may be a bug or unauthorized access, which fits orders (products/inventory) but needs immediate investigation. |
| T-1094 | Fraud warning on big order | sentiment | frustrated | neutral | A $1,900 order is flagged high risk for fraud and the customer is waiting on shipping, so the merchant needs a decision today to avoid losing the sale. |
| T-1094 | Fraud warning on big order | churn_risk | medium | low | A $1,900 order is flagged high risk for fraud and the customer is waiting on shipping, so the merchant needs a decision today to avoid losing the sale. |
| T-1060 | App deleted my products | sentiment | angry | frustrated | A bulk editing app wiped product descriptions for 300 products, an active problem blocking the merchant's work today, and the merchant is distressed but polite. |
| T-1060 | App deleted my products | churn_risk | high | medium | A bulk editing app wiped product descriptions for 300 products, an active problem blocking the merchant's work today, and the merchant is distressed but polite. |
| T-1019 | Identity verification keeps failing | churn_risk | medium | low | Merchant's payment identity verification keeps failing despite clear uploads, which is a broken process with a possible workaround but no confirmed loss of sales yet. |
| T-1042 | Lost orders because of checkout bug | sentiment | angry | frustrated | A checkout update broke the free shipping threshold, causing customers to be overcharged and the merchant to lose sales, and they are requesting compensation. |
| T-1042 | Lost orders because of checkout bug | churn_risk | high | medium | A checkout update broke the free shipping threshold, causing customers to be overcharged and the merchant to lose sales, and they are requesting compensation. |
| T-1099 | Return and exchange process | urgency | medium | low | The merchant asks how to handle an exchange workflow, a how-to question about orders with no active problem or urgency. |
| T-1057 | Connect to QuickBooks | urgency | medium | low | The merchant is asking a how-to question about syncing orders and payouts with QuickBooks, which is an integration question with no active problem. |
| T-1052 | Paid for theme that doesn't work | sentiment | angry | frustrated | Merchant paid $280 for the Atelier theme and half its demo features don't work on their store, a broken theme with a workaround such as a fix or refund request. |
| T-1023 | My website is DOWN | sentiment | angry | frustrated | The merchant's store site is unreachable during Black Friday week, actively losing sales, so it is urgent even though the merchant is frustrated rather than hostile. |
| T-1023 | My website is DOWN | churn_risk | high | medium | The merchant's store site is unreachable during Black Friday week, actively losing sales, so it is urgent even though the merchant is frustrated rather than hostile. |
| T-1090 | Inventory showing negative | churn_risk | medium | low | Inventory is wrong so orders are being taken for items the merchant doesn't have, an active problem costing sales and fulfilment time. |
| T-1054 | Store loads slowly | urgency | medium | low | A neutral how-to question about store speed, which may be caused by the theme, with no active sales impact reported. |
| T-1054 | Store loads slowly | sentiment | frustrated | neutral | A neutral how-to question about store speed, which may be caused by the theme, with no active sales impact reported. |
| T-1028 | Domain expired, store unreachable | urgency | high | urgent | The Storely-purchased domain expired and the store is unreachable, so customers cannot visit it, and the merchant is annoyed about the missing warning. |
| T-1028 | Domain expired, store unreachable | churn_risk | high | medium | The Storely-purchased domain expired and the store is unreachable, so customers cannot visit it, and the merchant is annoyed about the missing warning. |
| T-1024 | Connect a domain from GoDaddy | urgency | medium | low | The merchant is asking how-to steps for connecting an existing GoDaddy domain to their store, with no active problem. |
| T-1037 | High abandoned cart rate | sentiment | frustrated | neutral | Merchant reports a high abandoned cart rate at the shipping step, which may indicate a checkout issue but has a workaround and is a diagnostic question rather than an outage. |
| T-1037 | High abandoned cart rate | churn_risk | medium | low | Merchant reports a high abandoned cart rate at the shipping step, which may indicate a checkout issue but has a workaround and is a diagnostic question rather than an outage. |
| T-1088 | Store suspended without warning | urgency | high | urgent | The store is suspended with no details, blocking all sales, and the merchant threatens to take 4,000 customers elsewhere. |
| T-1008 | Change billing currency | urgency | medium | low | Merchant asks a how-to question about changing the subscription billing currency to CAD after moving to Canada, with no active problem or churn signals. |
| T-1043 | Checkout language wrong | urgency | medium | low | A how-to question about checkout page language settings with no sales impact or urgency. |
| T-1043 | Checkout language wrong | sentiment | frustrated | neutral | A how-to question about checkout page language settings with no sales impact or urgency. |
| T-1058 | Uninstalled app left code behind | urgency | medium | low | A merchant asks how to remove leftover code from an uninstalled popup app, a how-to question with a non-blocking display issue. |
| T-1058 | Uninstalled app left code behind | sentiment | frustrated | neutral | A merchant asks how to remove leftover code from an uninstalled popup app, a how-to question with a non-blocking display issue. |
| T-1058 | Uninstalled app left code behind | churn_risk | medium | low | A merchant asks how to remove leftover code from an uninstalled popup app, a how-to question with a non-blocking display issue. |
| T-1034 | Customers can't complete checkout | sentiment | angry | frustrated | Customers get errors at the payment step so the store cannot take orders, costing sales right now, and the merchant is worried about a platform outage. |
| T-1034 | Customers can't complete checkout | churn_risk | high | medium | Customers get errors at the payment step so the store cannot take orders, costing sales right now, and the merchant is worried about a platform outage. |
| T-1010 | Transaction fees are killing me | sentiment | angry | frustrated | Merchant is upset about an unexpected 2% transaction fee on PayPal orders costing hundreds monthly and is considering leaving the platform, so it is a billing issue with high churn risk but no sales blocked. |
| T-1064 | Build my own app? | sentiment | positive | neutral | The merchant is asking how-to documentation for building a private app for their own store, a low-urgency feature question with no problem reported. |
| T-1045 | Images look blurry | urgency | medium | low | A how-to question about image sizing for store design, with no sales or money impact. |
| T-1045 | Images look blurry | sentiment | frustrated | neutral | A how-to question about image sizing for store design, with no sales or money impact. |
| T-1031 | DNS changes not taking effect | sentiment | frustrated | neutral | DNS A record change is not propagating after 48 hours, a broken setup with a workaround, and the merchant is asking a neutral question about timing. |
| T-1031 | DNS changes not taking effect | churn_risk | medium | low | DNS A record change is not propagating after 48 hours, a broken setup with a workaround, and the merchant is asking a neutral question about timing. |
| T-1089 | Edit an order after purchase | urgency | medium | low | The merchant is asking how to edit an existing order's size, a how-to question with no active problem or money at risk. |
| T-1026 | www version doesn't work | sentiment | frustrated | neutral | The www subdomain shows an error while the root domain works, a domain/DNS setup problem with a workaround available, and the merchant sounds neutral with no churn signals. |
| T-1077 | Delivery date at checkout | urgency | medium | low | The merchant asks how to let customers choose a delivery date, a feature question with no active problem, so it is low urgency and shipping-related. |
| T-1016 | Accept Apple Pay | urgency | medium | low | A neutral how-to question about enabling Apple Pay and Google Pay, with no blocked sales or money at stake. |
