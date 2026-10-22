# Connect HubSpot

HubSpot is the helpdesk in this project. Its free plan includes a ticket inbox and API access, with no time limit and
no credit card. The app reads tickets from HubSpot and writes the AI's results back onto each ticket.

## 1. Create a free account

Go to [hubspot.com](https://www.hubspot.com) and click **Get started free**. Skip any offer to start a paid trial.

## 2. Create a private app and copy its token

You need to be a super admin, which you are on your own account.

1. Go to **Development**, then click **Legacy apps** in the left sidebar.
2. Click **Create legacy app**, then choose **Private**.
3. On **Basic Info**, name it `Support AI Assistant`.
4. On the **Scopes** tab, click **Add new scope**, tick these, then click **Update**:
   - `tickets`
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
5. Click **Create app**, then **Continue creating**.
6. Open the **Auth** tab, click **Show token**, then **Copy**.

HubSpot moves menus around from time to time. Their current guide is
[here](https://developers.hubspot.com/docs/apps/legacy-apps/private-apps/overview).

## 3. Add the token to `.env`

```
HUBSPOT_ACCESS_TOKEN=your-token
```

The token is a password to your HubSpot account. Keep it only in `.env`, which is never committed.

## 4. Load the tickets

```bash
python -m scripts.load_tickets_to_hubspot
```

This adds a **Storely AI** group of ticket properties, creates one contact per merchant, and creates the 100 tickets.
It also copies the AI results you already have from Google Sheets, so nothing needs to be paid for again. If HubSpot
says a scope is missing, the message names it: add it on the app's **Scopes** tab and run the command again.

## 5. Use HubSpot as the data source

In `.env`, set:

```
DATA_SOURCE=hubspot
```

Now `run_triage`, `run_answers`, the evaluations and the agent assist screen all read from and write to HubSpot.
Help articles still come from Google Drive, and the Google Sheet stays as a backup copy.
