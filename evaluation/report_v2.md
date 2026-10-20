# Triage accuracy report: version 2 instructions

The AI's answers for **100 tickets** compared with labels written by a person.

| Field | Exactly right | Right or one level off |
| --- | --- | --- |
| Category | 99% (99/100) | n/a |
| Urgency | 70% (70/100) | 100% |
| Sentiment | 84% (84/100) | 100% |
| Churn risk | 87% (87/100) | 100% |

## Escalations

Tickets that needed **Priority Escalations** (urgent, or angry with high churn risk): **12**.
The AI caught **11 of 12** (92%) and flagged 2 extra ticket(s) that didn't need it.

- Missed: T-1010 "Transaction fees are killing me" went to Billing

## Most common mistakes

- **Category** (correct → AI): payments → billing (1×)
- **Urgency** (correct → AI): medium → low (19×), medium → high (6×), high → urgent (4×), low → medium (1×)
- **Sentiment** (correct → AI): frustrated → neutral (10×), angry → frustrated (3×), positive → neutral (2×), neutral → frustrated (1×)
- **Churn risk** (correct → AI): medium → low (8×), high → medium (3×), medium → high (2×)

## Every mistake

| Ticket | Subject | Field | Correct | AI | AI's reason |
| --- | --- | --- | --- | --- | --- |
| T-1073 | Wrong shipping label address | churn_risk | medium | high | Shipping labels printed with the wrong return address are already on out-going packages and the merchant is demanding a refund, which signals high churn risk. |
| T-1063 | Inventory not syncing with Amazon | urgency | medium | high | The Amazon integration app is failing to sync inventory, which has already caused four oversold items and affects customers now. |
| T-1087 | Export customer list | urgency | medium | low | This is a plain how-to question about exporting customer data with nothing currently broken, so it is low urgency and the merchant is neutral with no churn signals. |
| T-1067 | Set up free shipping over $50 | urgency | medium | low | This is a how-to question about configuring shipping rates with nothing currently broken. |
| T-1040 | Guest checkout | urgency | medium | low | The merchant asks whether guest checkout can be enabled, a plain how-to question with no outage or money at stake, though some customers report friction. |
| T-1081 | Transfer store ownership | urgency | medium | low | Merchant asks how to transfer store ownership as part of selling the business, a plain how-to question with nothing currently broken, and the sale is a big change that raises churn risk. |
| T-1049 | Edit footer text | urgency | medium | low | A how-to question about editing footer copyright text in the theme, with nothing broken or urgent. |
| T-1001 | Charged twice this month | urgency | medium | high | Merchant was charged twice for the same Advanced subscription this month and is asking for the duplicate charge to be refunded, which involves a wrong charge and money at stake. |
| T-1001 | Charged twice this month | sentiment | frustrated | neutral | Merchant was charged twice for the same Advanced subscription this month and is asking for the duplicate charge to be refunded, which involves a wrong charge and money at stake. |
| T-1084 | Close my store | churn_risk | medium | high | Merchant wants to permanently close the store and asks about data deletion and export, a plain question with nothing broken, but closing the store signals high churn. |
| T-1086 | Multiple stores one login | sentiment | positive | neutral | A plain how-to question about managing two stores under one login, with nothing currently broken. |
| T-1007 | Store paused because payment failed | urgency | high | urgent | The store is frozen and customers cannot buy after an expired card, the merchant already updated the card and is losing sales, so the freeze needs to be lifted right away. |
| T-1095 | Pre-orders | urgency | medium | low | A plain how-to question about taking pre-orders for a future product, with nothing currently broken. |
| T-1079 | Not receiving 2FA code | urgency | medium | high | Merchant is locked out of their account after a carrier change and cannot receive the two-step verification code, which blocks store access. |
| T-1020 | Refund stuck in pending | sentiment | neutral | frustrated | A customer refund has been pending for 9 days with the customer repeatedly following up, which is a stuck refund affecting customer experience and money. |
| T-1061 | API access for my developer | urgency | medium | low | A plain how-to question about creating API credentials for a custom integration, with nothing currently broken. |
| T-1065 | Translation app conflicts with theme | sentiment | frustrated | neutral | A translation app is causing the menu to show two languages, a non-critical conflict with a clear question about who to contact. |
| T-1035 | Add a tip option at checkout | urgency | medium | low | This is a plain how-to question about adding a tip option at checkout with nothing currently broken. |
| T-1021 | Payment fees higher than expected | category | payments | billing | The merchant asks for a breakdown of fees taken from a payout, with no failure or urgent deadline, so this is a billing question about transaction fees. |
| T-1021 | Payment fees higher than expected | urgency | medium | low | The merchant asks for a breakdown of fees taken from a payout, with no failure or urgent deadline, so this is a billing question about transaction fees. |
| T-1021 | Payment fees higher than expected | sentiment | frustrated | neutral | The merchant asks for a breakdown of fees taken from a payout, with no failure or urgent deadline, so this is a billing question about transaction fees. |
| T-1015 | Customer chargeback, what do I do? | sentiment | frustrated | neutral | A customer chargeback with a response deadline puts money at stake, though the merchant is calmly asking how to submit evidence. |
| T-1015 | Customer chargeback, what do I do? | churn_risk | medium | low | A customer chargeback with a response deadline puts money at stake, though the merchant is calmly asking how to submit evidence. |
| T-1072 | Calculated carrier rates | urgency | medium | low | A plain how-to question about enabling live UPS carrier rates at checkout, with nothing currently broken. |
| T-1029 | Transfer domain to Storely | urgency | medium | low | Merchant asks how-to and fee questions about transferring a domain from Namecheap, with nothing currently broken. |
| T-1047 | Theme update broke my store | churn_risk | medium | low | A theme update just broke the homepage sections and menu on a live store, and the merchant wants to roll back, though they stay polite and make no threats. |
| T-1075 | Tracking numbers not sent to customers | urgency | medium | high | Tracking emails aren't reaching customers after fulfillment, so buyers are repeatedly asking where their orders are, which affects customers right now. |
| T-1085 | Staff member can't log in | sentiment | frustrated | neutral | A staff member's invitation link has expired, blocking her login, which is an account access issue that is not urgent or costing sales. |
| T-1097 | Duplicate orders from one customer | sentiment | frustrated | neutral | The merchant asks how to cancel a duplicate order and refund it correctly, a plain how-to question with no platform failure, though a customer was double charged. |
| T-1097 | Duplicate orders from one customer | churn_risk | medium | low | The merchant asks how to cancel a duplicate order and refund it correctly, a plain how-to question with no platform failure, though a customer was double charged. |
| T-1094 | Fraud warning on big order | sentiment | frustrated | neutral | A large order flagged as high fraud risk needs a decision before fulfillment, and the customer is waiting on shipping, but the tone is a plain question with no complaint. |
| T-1094 | Fraud warning on big order | churn_risk | medium | low | A large order flagged as high fraud risk needs a decision before fulfillment, and the customer is waiting on shipping, but the tone is a plain question with no complaint. |
| T-1060 | App deleted my products | urgency | high | urgent | A bulk editing app wiped product descriptions for 300 products, and the merchant calls it a disaster and asks for restoration, which is urgent data loss from an app. |
| T-1060 | App deleted my products | churn_risk | high | medium | A bulk editing app wiped product descriptions for 300 products, and the merchant calls it a disaster and asks for restoration, which is urgent data loss from an app. |
| T-1019 | Identity verification keeps failing | urgency | medium | high | Merchant's payment verification keeps failing after three attempts, which blocks payouts and payments, so it is frustrating and time-sensitive but not a platform outage. |
| T-1042 | Lost orders because of checkout bug | urgency | high | urgent | A platform checkout update broke the free shipping threshold, so customers are being overcharged and the merchant is losing sales while demanding compensation. |
| T-1099 | Return and exchange process | urgency | medium | low | The merchant asks how to handle an exchange with nothing broken, so it is a low-urgency how-to question about order handling. |
| T-1057 | Connect to QuickBooks | urgency | medium | low | This is a plain how-to question about integrating orders and payouts with QuickBooks, with nothing currently broken. |
| T-1052 | Paid for theme that doesn't work | sentiment | angry | frustrated | A paid theme's demo features don't work on the merchant's store, and they are asking for a refund or a fix, which is frustrating but not blocking sales. |
| T-1090 | Inventory showing negative | churn_risk | medium | low | Negative inventory is causing orders for items the merchant doesn't have, so customers are affected right now, though the tone is polite and no churn signals appear. |
| T-1054 | Store loads slowly | sentiment | frustrated | neutral | The merchant asks a plain question about slow load times, which may be caused by the theme, with no sign of lost sales or escalation. |
| T-1028 | Domain expired, store unreachable | churn_risk | high | medium | The store is unreachable because the Storely-purchased domain expired, and the merchant is frustrated they got no warning, though they can likely renew it themselves. |
| T-1024 | Connect a domain from GoDaddy | urgency | medium | low | A how-to question about connecting a GoDaddy domain with nothing currently broken and a polite, neutral tone. |
| T-1037 | High abandoned cart rate | sentiment | frustrated | neutral | Merchant asks why 70% of customers abandon at the shipping step, which may be a checkout problem but nothing is confirmed broken and no complaint or churn signal is given. |
| T-1037 | High abandoned cart rate | churn_risk | medium | low | Merchant asks why 70% of customers abandon at the shipping step, which may be a checkout problem but nothing is confirmed broken and no complaint or churn signal is given. |
| T-1093 | Product variants limit | urgency | low | medium | Merchant hit a product variant limit with 108 combinations and asks for options, which is a plain question with a product setup issue but nothing broken for customers yet. |
| T-1088 | Store suspended without warning | urgency | high | urgent | The store is suspended with no explanation and the merchant's appeal is unanswered, so they cannot sell, and they explicitly threaten to move their 4,000 customers elsewhere. |
| T-1008 | Change billing currency | urgency | medium | low | Merchant asks whether their Advanced subscription can switch from USD to CAD after relocating, with nothing currently broken. |
| T-1043 | Checkout language wrong | urgency | medium | low | A plain how-to question about changing the checkout page language, with nothing currently broken or blocking sales. |
| T-1043 | Checkout language wrong | sentiment | frustrated | neutral | A plain how-to question about changing the checkout page language, with nothing currently broken or blocking sales. |
| T-1058 | Uninstalled app left code behind | churn_risk | medium | low | A removed popup app's leftover code still displays on the store, a non-critical issue the merchant is trying to clear up themselves. |
| T-1034 | Customers can't complete checkout | sentiment | angry | frustrated | Customers cannot complete checkout due to a payment-step error, halting all sales for three hours, which points to a platform-side failure. |
| T-1034 | Customers can't complete checkout | churn_risk | high | medium | Customers cannot complete checkout due to a payment-step error, halting all sales for three hours, which points to a platform-side failure. |
| T-1010 | Transaction fees are killing me | sentiment | angry | frustrated | Merchant is upset about an unexpected 2% transaction fee on PayPal orders and is considering moving to another platform, which is a billing issue with high churn risk. |
| T-1064 | Build my own app? | sentiment | positive | neutral | A plain how-to question about building a private app for their own store, with nothing currently broken. |
| T-1031 | DNS changes not taking effect | churn_risk | medium | low | Merchant's A record change to Storely has not propagated after 48 hours, so the store's site still shows the old website, which is a non-critical delay with a polite tone. |
| T-1089 | Edit an order after purchase | urgency | medium | low | The merchant is asking how to edit an order after purchase with nothing broken, so it is a plain how-to question about order editing. |
| T-1026 | www version doesn't work | urgency | medium | high | The www subdomain of the store's domain errors while the root domain works, so customers may be hitting a broken site despite the merchant having followed the setup guide. |
| T-1077 | Delivery date at checkout | urgency | medium | low | A plain how-to question about offering delivery date selection at checkout, with nothing currently broken. |
| T-1016 | Accept Apple Pay | urgency | medium | low | Merchant asks how to enable Apple Pay and Google Pay, a how-to question with nothing currently broken. |
