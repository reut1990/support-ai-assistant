# Connect to Google Drive

This connects the app to a Google Sheet (tickets) and a Google Drive folder (help articles). Everything here is free: you don't need to add a credit card to Google Cloud.

It takes about 10 minutes.

## 1. Create a Google Cloud project
1. Go to [console.cloud.google.com](https://console.cloud.google.com) and sign in with your Google account.
2. If asked, accept the terms. You don't need to start a free trial or add billing.
3. Click the project picker at the top, then **New project**. Name it `support-ai-assistant` and click **Create**.
4. Make sure the new project is selected in the project picker.

## 2. Turn on the two APIs
1. Open [Google Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com) and click **Enable**.
2. Open [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com) and click **Enable**.

## 3. Create a service account and its key
A service account is a "robot" Google account that the app signs in as.
1. Go to **IAM & Admin > Service accounts** and click **Create service account**.
2. Name it `support-ai-app` and click **Create and continue**, then **Done**. Skip the optional role steps.
3. Copy the service account's email address. It looks like `support-ai-app@support-ai-assistant.iam.gserviceaccount.com`.
4. Click the service account, open the **Keys** tab, and choose **Add key > Create new key > JSON**. A file downloads.
5. In the project folder on your computer, create a folder called `credentials` and move the file there, renamed to `google-service-account.json`.

> ⚠️ This file is a password for the robot account. Never share it, email it or upload it to GitHub. The project's `.gitignore` already keeps the `credentials` folder out of GitHub.

## 4. Create the Sheet and folder in Google Drive
1. In [Google Drive](https://drive.google.com), create a folder called **Support AI Assistant**.
2. Inside it, create a Google Sheet called **Storely tickets**.
3. Also inside it, create a folder called **Help articles**, and upload the 15 `.md` files from `data/help_articles` (you can skip `README.md`).
4. Right-click the **Support AI Assistant** folder, choose **Share**, paste the service account email from step 3, set it to **Editor**, untick **Notify people**, and click **Share**.

## 5. Copy the two IDs into your settings
1. Copy `.env.example` to a new file called `.env` in the project folder.
2. Open the Sheet. Its address looks like `docs.google.com/spreadsheets/d/`**`1AbC...xyz`**`/edit`. Paste the bold part after `GOOGLE_SHEET_ID=`.
3. Open the **Help articles** folder. Its address looks like `drive.google.com/drive/folders/`**`1XyZ...abc`**. Paste the bold part after `GOOGLE_DRIVE_FOLDER_ID=`.

## 6. Load the tickets and test the connection
From the project folder:

```bash
pip install -r requirements.txt
python -m scripts.load_tickets_to_sheet
```

Open the Sheet: it now has a **Tickets** tab with 100 tickets. Then set `DATA_SOURCE=google` in `.env` and run:

```bash
python -m scripts.check_connection
```

You should see:

```
Data source: google
Tickets:  100  ...
Articles: 15  ...
Connection OK
```

When the AI triages a ticket in later steps, its answers appear in new columns (`ai_category`, `ai_urgency` and so on) next to each ticket in the Sheet.

## Troubleshooting
- **`FileNotFoundError: Google key file not found`:** the key isn't at `credentials/google-service-account.json`.
- **`PERMISSION_DENIED` or `404`:** the folder isn't shared with the service account email, or an ID in `.env` is wrong.
- **`API has not been used in project`:** one of the APIs in step 2 isn't enabled. Enable it and wait a minute.
