# Reply drafting report: version 2 instructions

Replies drafted from the help articles for **100 tickets**.

| Check | Result |
| --- | --- |
| Said "I don't know" when no article covers the topic | 5 of 5 |
| Answered tickets that an article covers | 80 of 95 (84%) |
| Answers citing an article from the ticket's correct category | 78 of 80 (98%) |

## Handed to a person although an article may cover it

| Ticket | Subject | What the AI said was missing |
| --- | --- | --- |
| T-1082 | Change store email | The articles do not explain where or how to change the sender or reply-to email address shown on order confirmation emails. They cover shipping, orders, discounts and checkout, but not store email or notification sender settings. |
| T-1044 | Minimum order amount | The articles state that Storely does not support minimum order amounts without an app, but they do not name a specific app or describe any other supported method for setting a $25 minimum. The specialist should confirm which apps are recommended, whether any native option exists on the Grow plan, and how to configure a minimum order amount. |
| T-1030 | Set up custom email | The articles only mention that Storely does not host email inboxes and offers free email forwarding for addresses like hello@yourbrand.com to an inbox you already have. They do not state whether a full mailbox can be hosted with Storely or whether a separate email provider is required, so the agent should confirm what Storely supports for custom email on the Advanced plan. |
| T-1055 | Love the new editor | The provided articles do not describe how to schedule a homepage banner or any date-based scheduling for homepage sections. KB-501 covers editing the theme and adding, removing or reordering homepage sections, but not scheduling content changes. |
| T-1048 | Recommend a theme for jewelry | The articles describe how to edit, restore, and troubleshoot themes, and mention free and paid themes, but do not list or recommend any themes for a minimal jewelry store. Information on available theme styles or recommendations is needed from a specialist. |
| T-1096 | Sales report by product | The provided articles do not describe a sales report by product or where to find product sales reporting in Storely. They cover orders, inventory, taxes, discounts and checkout only. |
| T-1059 | Email marketing app recommendation | The articles do not list or recommend any email marketing apps, nor describe their compatibility with Storely. They only mention that abandoned checkout recovery emails can be turned on in Settings > Notifications > Abandoned checkout, and that apps are built by independent developers. A specialist should confirm which email marketing apps are compatible and how they integrate. |
| T-1072 | Calculated carrier rates | The articles state that carrier-calculated rates from carriers like UPS are available on Grow and Advanced plans, but the merchant is on the Basic plan. They do not say whether a Basic-plan store can use carrier-calculated rates, what options exist on Basic, or whether a plan upgrade is required. A specialist should confirm eligibility for UPS live rates on the Basic plan and the steps to set them up. |
| T-1085 | Staff member can't log in | The articles explain that invitation links expire after 7 days and that you can resend one from the staff member's page using Resend invite, but they don't cover how to handle a link that has already expired in a way that differs from that. Please confirm whether the resend step resolves this for the merchant, or whether a specialist needs to investigate a problem with the invitation itself. |
| T-1100 | All my products disappeared | The articles say that if products are missing and the activity log shows no changes by you or your staff, the merchant should contact Technical Support urgently. The articles do not describe how to restore deleted products or what caused the disappearance. The merchant has not yet checked the Products page filters or the activity log, and the articles do not confirm whether the products were deleted, set to Draft, or removed from the Online Store sales channel. The agent should check the activity log and escalate to Technical Support urgently. |
| T-1060 | App deleted my products | The articles state that Storely cannot undo changes an app makes to products and that the merchant should contact the app developer first, since many bulk editing apps keep a backup. They do not say whether Storely can restore the descriptions, nor describe any Storely-side recovery option. The app's name and developer contact are also not known. The specialist should confirm whether any Storely-side restore is possible, and help the merchant check for a backup from the app developer or a CSV export, if one exists. |
| T-1042 | Lost orders because of checkout bug | The articles describe how to set up free shipping conditional rates and troubleshoot checkout, but contain no information about a checkout update causing incorrect shipping charges, known bugs or incidents, or any compensation policy. The agent should check whether a known issue exists for the recent checkout update, verify the merchant's shipping rate configuration in Settings > Shipping and delivery, and review the compensation request, which the articles do not address. |
| T-1008 | Change billing currency | KB-101 says CAD is one of the supported billing currencies and that currency changes are requested through Billing Support, effective from the next billing cycle. However, the articles do not describe eligibility conditions for changing currency after a country move, whether the change can be made directly by the merchant, or any timeframe for the change, so a specialist should confirm whether the change can be made for Juniper Market's Advanced plan. |
| T-1076 | Customs forms | The articles only say that labels bought through Storely for international orders include customs information from each product's customs details, and that these should be filled in on each product page. They do not say whether customs forms are needed for UK shipments, whether Storely generates or submits any customs forms, or which labels or carriers support UK shipping (create shipping label is listed for US and Canada only). A specialist needs to confirm the UK customs process for Maple Market on the Basic plan. |
| T-1051 | Add a size chart | The articles do not explain how to add a size chart popup to product pages. They cover orders, inventory, shipping, tracking, apps and API access, but nothing on product page customization, size charts, popups, or theme editing. A specialist should advise on whether this needs a theme change, a size chart app, or a built-in feature. |

## Answers citing an article from another category

Not always wrong: a ticket labeled *apps* can be answered by the orders article, for example.

| Ticket | Subject | Correct category | Cited |
| --- | --- | --- | --- |
| T-1063 | Inventory not syncing with Amazon | apps | KB-901 |
| T-1021 | Payment fees higher than expected | payments | KB-103 |

## Sample replies

### T-1073: Wrong shipping label address

> I bought 12 labels through Storely and they all printed with my old return address. The packages are already out. I want a refund for the labels.

Hello Noah,

Thank you for contacting Storely Support. You bought 12 shipping labels through Storely, and they printed with your old return address.

Your return address on shipping labels comes from Settings > Locations, so the labels use whatever address is saved there when you buy them. Labels that were already bought with the old address will not change automatically.

To check and fix this for future labels:
1. Open Settings > Locations and update your return address.
2. Confirm the new address before you buy any more labels.

Labels can be voided for a refund within 28 days if they haven't been used. Since your packages have already gone out, a refund depends on whether the labels meet that condition, so please check with the team before promising one to the merchant.

For more details, please see our help article “Shipping rates, zones, local pickup and tracking”.

Kind regards,
Storely Support Team

*Sources: KB-701*

### T-1063: Inventory not syncing with Amazon

> My Amazon integration app isn't syncing inventory. I oversold 4 items yesterday.

Hello Priya,

Thank you for contacting Storely Support. Your Amazon integration app is not syncing inventory, which has led to 4 items being oversold.

When you sell on other channels through an app, the app may be updating inventory too, so its sync settings may be the cause.

To stop overselling while you check the sync, please follow these steps:
1. Open the affected product and turn on Track quantity.
2. Turn off Continue selling when out of stock.
3. Check the sync settings in your Amazon integration app.

If the inventory continues to be out of sync after these steps, please reply to this message and our team will assist you further.

For more details, please see our help article “Manage orders, inventory and fraud risk”.

Kind regards,
Storely Support Team

*Sources: KB-901*

### T-1087: Export customer list

> How do I export all my customers with their email marketing consent?

Hello Hannah,

Thank you for contacting Storely Support. You would like to export your full customer list, including each customer's email marketing consent.

You can export your customers, including marketing consent, from the customers page using the Export option.

We recommend the following steps:
1. Open your customers page in your Storely admin.
2. Click Export and choose the customers export that includes marketing consent.
3. Download the file once the export is ready.

If the export does not include the consent information you need, please reply to this message and we will assist you further.

For more details, please see our help article “Account security, login problems and staff access”.

Kind regards,
Storely Support Team

*Sources: KB-801*

### T-1067: Set up free shipping over $50

> How do I offer free shipping for orders over $50 but keep flat rate shipping below that?

Hello Diego,

Thank you for contacting Storely Support. You would like to offer free shipping on orders over $50 while keeping flat rate shipping for smaller orders.

You can do this with two rates in the same shipping zone, using a conditional rate for the free shipping threshold.

1. Go to Settings > Shipping and delivery.
2. Open the zone you want to edit and click Add rate.
3. Add a flat rate for orders from $0 to $49.99.
4. Add a second rate called Free shipping at $0, with the condition Order price from $50.

If the rates do not show as expected at checkout, please reply to this message and our team will be glad to help further.

For more details, please see our help article “Shipping rates, zones, local pickup and tracking”.

Kind regards,
Storely Support Team

*Sources: KB-701*

### T-1040: Guest checkout

> Some customers say they're forced to create an account. Can I allow checkout without an account?

Hello Priya,

Thank you for contacting Storely Support. You would like to allow customers to check out without creating an account on your Harbor Co store.

You can enable guest checkout by changing the customer account setting, so that accounts are optional for shoppers.

1. Go to Settings > Checkout > Customer accounts.
2. Choose Accounts are optional.

Once saved, customers can complete checkout without creating an account. If customers still report being forced to create an account, please reply to this message so we can look into it further.

For more details, please see our help article “Discount codes and checkout problems”.

Kind regards,
Storely Support Team

*Sources: KB-401*

### T-1062: Sell on Instagram

> How do I connect my store to Instagram so I can tag products in posts?

Hello Leila,

Thank you for contacting Storely Support. You would like to connect your store to Instagram so you can tag products in your posts.

I have forwarded your request to a specialist on our team, who will follow up with you directly.

Kind regards,
Storely Support Team

*Handed to a person*

### T-1095: Pre-orders

> Can I take pre-orders for a product that launches next month?

Hello Omar,

Thank you for contacting Storely Support. You asked whether you can take pre-orders for a product that launches next month.

I have forwarded your request to a specialist on our team, who will follow up with you directly.

Kind regards,
Storely Support Team

*Handed to a person*
