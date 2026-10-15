---
id: KB-302
title: SSL certificates, expired domains and sites that won't load
category: domains
---

# SSL certificates, expired domains and sites that won't load

## SSL ("Not secure" warning)
Storely issues a free SSL certificate for every connected domain. The certificate is issued automatically once your DNS records are correct, usually within an hour and always within **48 hours**.

If it's been more than 48 hours:
1. Check your DNS records match **Connect a domain you bought somewhere else** exactly.
2. Remove any **AAAA records** for `@` or `www`. They block certificate issuing.
3. Go to **Settings > Domains** and click **Retry SSL**.

## Site can't be reached
1. Check status.storely.example for a platform-wide outage.
2. Open your store using its `.storely.example` address. If that works, the problem is your domain or DNS.
3. Check that your domain hasn't expired with your provider.
4. Check that your DNS records haven't been changed.

If your `.storely.example` address also doesn't load and there's no reported outage, contact Technical Support urgently.

## Expired domain
Domains bought through Storely renew automatically unless auto-renew was turned off. Renewal reminders are sent 30, 7 and 1 day before expiry to the store owner's email.

After a domain expires, there's a **30-day grace period**. Renew it in **Settings > Domains** at the normal price, and the store is reachable again within a few hours. After 30 days, a recovery fee applies.

## Email addresses on your domain
Storely doesn't host email inboxes. You can set up free **email forwarding** in **Settings > Domains > Email forwarding**, which sends messages for addresses like `hello@yourbrand.com` to an inbox you already have.
