"""Builds data/tickets/tickets.csv from the hand-written tickets below.

Every ticket was written for this project. The platform ("Storely"), merchants,
stores and email addresses are fictional.

Labels (the "correct answers" used to measure the AI later):
  category   billing | payments | domains | checkout | themes | apps |
             shipping | account | orders
  urgency    low | medium | high | urgent
  sentiment  positive | neutral | frustrated | angry
  churn_risk low | medium | high
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# (category, urgency, sentiment, churn_risk, subject, body)
TICKETS = [
    # --- billing -----------------------------------------------------------
    ("billing", "medium", "frustrated", "medium",
     "Charged twice this month",
     "Hi, I see two charges of $39 for my Storely subscription on my card statement this month. "
     "I only have one store. Can you refund the duplicate please?"),
    ("billing", "low", "neutral", "low",
     "How do I download invoices?",
     "Where can I find my invoices for the last 6 months? My accountant needs them for tax filing."),
    ("billing", "high", "angry", "high",
     "Cancel my plan and refund me NOW",
     "I asked to cancel last week and you still charged me $105 for the Advanced plan. "
     "This is unacceptable. Refund me today or I'm disputing it with my bank."),
    ("billing", "low", "neutral", "medium",
     "Downgrade from Advanced to Basic",
     "Sales have been slow this season so I'd like to move to the Basic plan. "
     "Will I lose my reports or any of my apps if I downgrade?"),
    ("billing", "medium", "frustrated", "medium",
     "App charges on my bill I don't recognize",
     "My bill has $27.99 in app charges but I uninstalled all those apps weeks ago. "
     "Why am I still paying for them?"),
    ("billing", "low", "positive", "low",
     "Annual plan discount?",
     "Loving Storely so far! Is there a discount if I switch to yearly billing instead of monthly?"),
    ("billing", "high", "frustrated", "high",
     "Store paused because payment failed",
     "My card expired and now my store is frozen. I updated the card but the store is still frozen "
     "and customers can't buy anything. Please unfreeze it, I'm losing sales."),
    ("billing", "medium", "neutral", "low",
     "Change billing currency",
     "I moved my business from the US to Canada. Can my subscription be billed in CAD instead of USD?"),
    ("billing", "low", "neutral", "low",
     "VAT number on invoice",
     "Can you add my company's VAT number to my invoices? We're registered in Germany."),
    ("billing", "medium", "angry", "high",
     "Transaction fees are killing me",
     "Nobody told me I'd pay an extra 2% on every order for using PayPal instead of Storely Payments. "
     "That's hundreds of dollars a month. Honestly thinking about moving to another platform."),
    ("billing", "low", "neutral", "medium",
     "Pause store while I travel",
     "I'm traveling for two months. Is there a cheaper plan to keep my store online but closed for orders?"),

    # --- payments ----------------------------------------------------------
    ("payments", "urgent", "angry", "high",
     "Payouts on hold for 10 days",
     "My payouts have been on hold for 10 days with no explanation. I have $8,400 sitting there and I "
     "need to pay my suppliers on Friday. This is my livelihood. Release my money or tell me why."),
    ("payments", "high", "frustrated", "medium",
     "Payout didn't arrive",
     "The payout scheduled for Monday says 'paid' but it's not in my bank account. It's Wednesday now. "
     "Bank says nothing incoming."),
    ("payments", "medium", "neutral", "low",
     "Change bank account for payouts",
     "I switched banks. How do I update the account my payouts go to? Will a pending payout be affected?"),
    ("payments", "high", "frustrated", "medium",
     "Customer chargeback, what do I do?",
     "A customer filed a chargeback saying they never got their order but tracking shows delivered. "
     "How do I submit evidence and how long do I have?"),
    ("payments", "medium", "neutral", "low",
     "Accept Apple Pay",
     "How do I turn on Apple Pay and Google Pay at checkout? I don't see the option."),
    ("payments", "urgent", "angry", "high",
     "Storely Payments account deactivated",
     "I just got an email that my Storely Payments account is deactivated for 'high risk'. I sell candles. "
     "Candles! I have orders coming in right now that I can't capture. Fix this immediately."),
    ("payments", "low", "positive", "low",
     "Payout schedule question",
     "Quick question, can I get payouts daily instead of weekly? Thanks for the great platform."),
    ("payments", "medium", "frustrated", "medium",
     "Identity verification keeps failing",
     "I've uploaded my driver's license three times for payment verification and it keeps saying "
     "'unable to verify'. The photo is clear. What am I doing wrong?"),
    ("payments", "high", "neutral", "medium",
     "Refund stuck in pending",
     "I issued a refund to a customer 9 days ago and it still shows pending. The customer is emailing "
     "me every day. When will it go through?"),
    ("payments", "medium", "frustrated", "low",
     "Payment fees higher than expected",
     "My payout was $47 less than my sales total. Can you break down which fees were taken?"),
    ("payments", "low", "neutral", "low",
     "Accept payments in multiple currencies",
     "I have customers in the UK and EU. Can they pay in GBP and EUR while I get paid in USD?"),

    # --- domains -----------------------------------------------------------
    ("domains", "urgent", "angry", "high",
     "My website is DOWN",
     "My domain shows 'site can't be reached' since this morning. It's Black Friday week. "
     "Every hour down is money gone. I need this fixed right now."),
    ("domains", "medium", "neutral", "low",
     "Connect a domain from GoDaddy",
     "I bought mybakeryshop.com on GoDaddy. How do I connect it to my Storely store?"),
    ("domains", "high", "frustrated", "medium",
     "SSL certificate not working",
     "Customers are getting a 'not secure' warning on my store. I connected my domain 3 days ago. "
     "Why isn't SSL active yet?"),
    ("domains", "medium", "frustrated", "low",
     "www version doesn't work",
     "mystore.com works but www.mystore.com gives an error. I followed the guide exactly."),
    ("domains", "low", "neutral", "low",
     "Change primary domain",
     "I have two domains connected. How do I make the .co.uk one the main one customers see?"),
    ("domains", "high", "frustrated", "high",
     "Domain expired, store unreachable",
     "I bought my domain through Storely and it expired without any warning email. Now the store is "
     "unreachable. Can I renew it? I had no idea auto-renew was off."),
    ("domains", "medium", "neutral", "low",
     "Transfer domain to Storely",
     "I'd like to transfer my domain from Namecheap so I can manage everything in one place. What are the steps and is there a fee?"),
    ("domains", "low", "neutral", "low",
     "Set up custom email",
     "Can I get an email like hello@mybrand.com through Storely, or do I need a separate provider?"),
    ("domains", "medium", "frustrated", "medium",
     "DNS changes not taking effect",
     "I changed my A record to point to Storely 48 hours ago and it still shows my old website. "
     "How long does this take?"),
    ("domains", "low", "positive", "low",
     "Subdomain for wholesale",
     "Hi team! Can I set up wholesale.mybrand.com as a separate storefront for my B2B customers?"),
    ("domains", "high", "angry", "high",
     "Third time asking about my domain",
     "This is the THIRD time I'm writing about my domain not connecting. Every agent gives me a different "
     "answer. I'm paying for Advanced and getting worse support than free plans elsewhere."),

    # --- checkout ----------------------------------------------------------
    ("checkout", "urgent", "angry", "high",
     "Customers can't complete checkout",
     "Since about 2pm customers get an error on the payment step and can't place orders. I've had 0 orders "
     "in 3 hours when I usually get 20. Is Storely down?"),
    ("checkout", "medium", "neutral", "low",
     "Add a tip option at checkout",
     "I run a local coffee roaster. Can I let customers add a tip at checkout?"),
    ("checkout", "high", "frustrated", "medium",
     "Discount code not applying",
     "My discount code SUMMER20 says 'not valid' for customers even though it's active and not expired. "
     "I've had 6 complaints today."),
    ("checkout", "medium", "frustrated", "medium",
     "High abandoned cart rate",
     "70% of my customers abandon at the shipping step. Is something broken or is shipping just too expensive? "
     "How can I see what's happening?"),
    ("checkout", "low", "neutral", "low",
     "Customize checkout fields",
     "I need customers to enter a gift message at checkout. Is that possible?"),
    ("checkout", "high", "frustrated", "medium",
     "Tax calculated wrong",
     "Checkout is charging 0% sales tax for customers in New York. I set up tax collection for NY. "
     "I'm going to owe this out of pocket."),
    ("checkout", "medium", "neutral", "low",
     "Guest checkout",
     "Some customers say they're forced to create an account. Can I allow checkout without an account?"),
    ("checkout", "low", "positive", "low",
     "Express checkout buttons",
     "Hi! I've seen stores with a 'Buy now' express button on the product page. How do I add that?"),
    ("checkout", "high", "angry", "high",
     "Lost orders because of checkout bug",
     "Your checkout update yesterday broke my free shipping threshold. Customers got charged shipping "
     "and are furious. I want compensation for this."),
    ("checkout", "medium", "frustrated", "low",
     "Checkout language wrong",
     "My store is in French but the checkout page shows in English. How do I fix this?"),
    ("checkout", "low", "neutral", "low",
     "Minimum order amount",
     "Can I set a minimum order of $25 before customers can check out?"),

    # --- themes ------------------------------------------------------------
    ("themes", "medium", "frustrated", "low",
     "Images look blurry",
     "My product images look blurry on the homepage even though I uploaded high resolution files. "
     "What size should they be?"),
    ("themes", "low", "neutral", "low",
     "Change fonts",
     "How do I change the font on my store headings? I want something more modern."),
    ("themes", "high", "frustrated", "medium",
     "Theme update broke my store",
     "I clicked 'update theme' and now my homepage sections are gone and the menu is broken. "
     "How do I go back to the previous version?"),
    ("themes", "low", "positive", "low",
     "Recommend a theme for jewelry",
     "I'm launching a handmade jewelry brand next month! Which theme would you recommend for a minimal look?"),
    ("themes", "medium", "neutral", "low",
     "Edit footer text",
     "Where do I edit the copyright text in my footer? It still says the theme name."),
    ("themes", "medium", "frustrated", "medium",
     "Mobile layout is broken",
     "On phones, my product pages show the add to cart button off the screen. Most of my traffic is mobile."),
    ("themes", "low", "neutral", "low",
     "Add a size chart",
     "How can I add a size chart popup to my clothing product pages?"),
    ("themes", "medium", "angry", "medium",
     "Paid for theme that doesn't work",
     "I paid $280 for the Atelier theme and half the features in the demo don't work on my store. "
     "I want a refund or a fix."),
    ("themes", "low", "neutral", "low",
     "Custom CSS",
     "Is it OK to edit the theme code to add custom CSS? Will it be overwritten when the theme updates?"),
    ("themes", "medium", "frustrated", "low",
     "Store loads slowly",
     "My store takes 6 seconds to load. Is it my theme? How can I speed it up?"),
    ("themes", "low", "positive", "low",
     "Love the new editor",
     "Just wanted to say the new drag and drop editor is great. One question: can I schedule a homepage "
     "banner to change on a specific date?"),

    # --- apps --------------------------------------------------------------
    ("apps", "high", "frustrated", "medium",
     "Reviews app stopped showing reviews",
     "My product reviews disappeared from all product pages after I installed another app. "
     "Reviews are a big part of how I sell."),
    ("apps", "medium", "neutral", "low",
     "Connect to QuickBooks",
     "Is there a way to sync my orders and payouts with QuickBooks automatically?"),
    ("apps", "medium", "frustrated", "medium",
     "Uninstalled app left code behind",
     "I uninstalled a popup app but the popup still shows on my store. How do I get rid of it?"),
    ("apps", "low", "neutral", "low",
     "Email marketing app recommendation",
     "Which email marketing apps work best with Storely for abandoned cart emails?"),
    ("apps", "high", "angry", "high",
     "App deleted my products",
     "A bulk editing app I installed wiped the descriptions of 300 products. Can Storely restore them? "
     "This is a disaster."),
    ("apps", "medium", "neutral", "low",
     "API access for my developer",
     "My developer needs API access to build a custom integration with our warehouse. How do I create API credentials?"),
    ("apps", "low", "neutral", "low",
     "Sell on Instagram",
     "How do I connect my store to Instagram so I can tag products in posts?"),
    ("apps", "medium", "frustrated", "medium",
     "Inventory not syncing with Amazon",
     "My Amazon integration app isn't syncing inventory. I oversold 4 items yesterday."),
    ("apps", "low", "positive", "low",
     "Build my own app?",
     "I'm a developer and a store owner. Is there documentation for building a private app for my own store?"),
    ("apps", "medium", "frustrated", "low",
     "Translation app conflicts with theme",
     "Since I installed a translation app my menu shows in two languages at once. Who do I contact, you or the app developer?"),
    ("apps", "low", "neutral", "low",
     "Too many apps slowing store?",
     "I have 23 apps installed. Could that be slowing down my store?"),

    # --- shipping ----------------------------------------------------------
    ("shipping", "medium", "neutral", "low",
     "Set up free shipping over $50",
     "How do I offer free shipping for orders over $50 but keep flat rate shipping below that?"),
    ("shipping", "high", "frustrated", "medium",
     "Shipping rates showing $0",
     "Customers outside the US are seeing $0 shipping at checkout. I've shipped 5 international orders "
     "at a loss this week."),
    ("shipping", "low", "neutral", "low",
     "Print shipping labels",
     "Can I buy and print USPS shipping labels directly from Storely?"),
    ("shipping", "medium", "frustrated", "low",
     "Local pickup option",
     "I added local pickup in settings but it doesn't appear at checkout. What am I missing?"),
    ("shipping", "low", "neutral", "low",
     "Ship to specific countries only",
     "I only want to ship to the US and Canada. How do I block other countries?"),
    ("shipping", "medium", "neutral", "low",
     "Calculated carrier rates",
     "Can I show live UPS rates at checkout instead of my own flat rates?"),
    ("shipping", "high", "angry", "medium",
     "Wrong shipping label address",
     "I bought 12 labels through Storely and they all printed with my old return address. The packages "
     "are already out. I want a refund for the labels."),
    ("shipping", "low", "positive", "low",
     "Shipping profiles for heavy items",
     "Thanks for the help last week! Now I want furniture items to have a different shipping rate than "
     "small decor. How do I do that?"),
    ("shipping", "medium", "frustrated", "low",
     "Tracking numbers not sent to customers",
     "When I mark orders as fulfilled, customers aren't getting the tracking email. They keep asking me "
     "where their order is."),
    ("shipping", "low", "neutral", "low",
     "Customs forms",
     "Do I need to fill in customs forms for shipping to the UK? Does Storely do this automatically?"),
    ("shipping", "medium", "neutral", "low",
     "Delivery date at checkout",
     "Can customers choose a delivery date at checkout? I sell fresh flowers."),

    # --- account -----------------------------------------------------------
    ("account", "urgent", "angry", "high",
     "Someone hacked my account",
     "I got an email that my login email was changed and I didn't do it. I can't log in anymore. "
     "Someone has access to my store and my payouts. Please lock it NOW."),
    ("account", "medium", "frustrated", "low",
     "Not receiving 2FA code",
     "I'm not getting the two-step verification text message so I can't log in. I changed phone carriers last week."),
    ("account", "low", "neutral", "low",
     "Add staff account",
     "How do I give my assistant access to orders without letting them see my financial reports?"),
    ("account", "medium", "neutral", "medium",
     "Transfer store ownership",
     "I'm selling my business. How do I transfer the store to the new owner?"),
    ("account", "low", "neutral", "low",
     "Change store email",
     "How do I change the email address customers see on order confirmations?"),
    ("account", "high", "frustrated", "medium",
     "Locked out after password reset",
     "I reset my password and now it says my account is locked. I have orders to fulfill today."),
    ("account", "low", "neutral", "medium",
     "Close my store",
     "I want to close my store permanently. Will my customer data be deleted? Can I export it first?"),
    ("account", "medium", "frustrated", "low",
     "Staff member can't log in",
     "I invited my employee as staff but she says the invitation link is expired."),
    ("account", "low", "positive", "low",
     "Multiple stores one login",
     "I'm opening a second store for a new brand. Can I manage both with one login?"),
    ("account", "medium", "neutral", "low",
     "Export customer list",
     "How do I export all my customers with their email marketing consent?"),
    ("account", "high", "angry", "high",
     "Store suspended without warning",
     "My store was suspended for 'policy violation' with no details. I sell vintage clothing, nothing illegal. "
     "Nobody replies to my appeal. I'll take my 4,000 customers elsewhere."),

    # --- orders ------------------------------------------------------------
    ("orders", "medium", "neutral", "low",
     "Edit an order after purchase",
     "A customer wants to change the size on an order they placed an hour ago. Can I edit the order or do I need to refund and redo it?"),
    ("orders", "high", "frustrated", "medium",
     "Inventory showing negative",
     "Several products show -3 or -5 inventory and orders keep coming in for items I don't have."),
    ("orders", "low", "neutral", "low",
     "Bulk import products",
     "I have 500 products in a spreadsheet. How do I import them all at once?"),
    ("orders", "medium", "frustrated", "low",
     "Order notifications not arriving",
     "I'm not getting email notifications for new orders anymore. I check spam, nothing."),
    ("orders", "low", "neutral", "low",
     "Product variants limit",
     "My t-shirt comes in 12 colors and 9 sizes. It says I hit the variant limit. What can I do?"),
    ("orders", "high", "frustrated", "medium",
     "Fraud warning on big order",
     "I got a $1,900 order marked high risk for fraud. Should I fulfill it? The customer is asking when it ships."),
    ("orders", "medium", "neutral", "low",
     "Pre-orders",
     "Can I take pre-orders for a product that launches next month?"),
    ("orders", "low", "positive", "low",
     "Sales report by product",
     "I'd love to see which products sold best this quarter. Where's that report?"),
    ("orders", "medium", "frustrated", "medium",
     "Duplicate orders from one customer",
     "A customer was charged twice and I have two identical orders. How do I cancel one and refund correctly?"),
    ("orders", "low", "neutral", "low",
     "Draft orders for phone sales",
     "Sometimes customers call me to order. Can I create an order for them and send a payment link?"),
    ("orders", "medium", "neutral", "low",
     "Return and exchange process",
     "What's the best way to handle exchanges? I want the customer to send the item back and get a different size."),
    ("orders", "urgent", "angry", "high",
     "All my products disappeared",
     "I logged in and my store has 0 products. I had 180 this morning. Nothing on the storefront. "
     "I haven't touched anything. What happened??"),
]

FIRST_NAMES = ["Maya", "Daniel", "Priya", "Lucas", "Amara", "Noah", "Sofia", "Ethan", "Leila", "Marcus",
               "Hannah", "Diego", "Yuki", "Omar", "Chloe", "Ravi", "Grace", "Tomas", "Nadia", "Ben"]
LAST_NAMES = ["Cohen", "Okafor", "Patel", "Silva", "Nguyen", "Brooks", "Rossi", "Kim", "Haddad", "Larsen",
              "Murphy", "Garcia", "Tanaka", "Schmidt", "Dubois", "Levy", "Mensah", "Novak", "Ali", "Reyes"]
STORE_WORDS = ["Bloom", "Craft", "Harbor", "Maple", "Nomad", "Pebble", "Saffron", "Tidal", "Willow", "Juniper"]
STORE_TYPES = ["Studio", "Goods", "Co", "Market", "Supply", "Boutique", "Shop", "House"]
PLANS = ["Basic", "Basic", "Grow", "Grow", "Advanced"]
CHANNELS = ["email", "email", "chat", "web form"]


def build(seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    start = datetime(2026, 10, 1, 8, 0)
    rows = []
    for i, (category, urgency, sentiment, churn, subject, body) in enumerate(TICKETS, start=1):
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        store = f"{rng.choice(STORE_WORDS)} {rng.choice(STORE_TYPES)}"
        created = start + timedelta(minutes=rng.randint(0, 14 * 24 * 60))
        rows.append({
            "ticket_id": f"T-{1000 + i}",
            "created_at": created.strftime("%Y-%m-%d %H:%M"),
            "customer_name": f"{first} {last}",
            "customer_email": f"{first.lower()}.{last.lower()}@example.com",
            "store_name": store,
            "plan": rng.choice(PLANS),
            "channel": rng.choice(CHANNELS),
            "subject": subject,
            "body": body,
            "label_category": category,
            "label_urgency": urgency,
            "label_sentiment": sentiment,
            "label_churn_risk": churn,
        })
    rows.sort(key=lambda r: r["created_at"])
    return rows


if __name__ == "__main__":
    out = Path(__file__).with_name("tickets.csv")
    rows = build()
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} tickets to {out}")
