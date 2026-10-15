---
id: KB-301
title: Connect a domain you bought somewhere else
category: domains
---

# Connect a domain you bought somewhere else

You can keep your domain with your current provider (such as GoDaddy or Namecheap) and point it to Storely.

## Steps
1. In Storely, go to **Settings > Domains > Connect existing domain** and enter your domain.
2. Sign in to your domain provider and open the DNS settings.
3. Change the **A record** for `@` to `203.0.113.10`.
4. Change the **CNAME record** for `www` to `stores.storely.example`.
5. Remove any other A records for `@` and `www`.
6. Return to Storely and click **Verify connection**.

DNS changes can take **up to 48 hours** to take effect worldwide, but usually work within an hour.

## Common problems
- **The www version doesn't work:** the `www` CNAME record is missing or points to the old host. Check step 4.
- **The old website still shows after 48 hours:** an old A record is still there, or your provider uses its own nameservers with a separate DNS panel. Check that only one A record exists for `@`.
- **The domain is connected but shows an error:** check that the domain is set as **Primary** in **Settings > Domains**.

## Change the primary domain
If several domains are connected, the primary domain is the one customers see in the address bar. Go to **Settings > Domains**, click **Change primary domain**, and choose one. All other domains redirect to it.

## Transfer your domain to Storely
Transferring moves billing and DNS management to Storely. Go to **Settings > Domains > Transfer domain**. You'll need the transfer code from your current provider. Transfers cost the price of one year's renewal and take 5 to 7 days.

## Subdomains
You can connect subdomains, such as `shop.yourbrand.com`, the same way using a CNAME record. Each store can only use one storefront, so a separate storefront on a subdomain needs a separate Storely store.
