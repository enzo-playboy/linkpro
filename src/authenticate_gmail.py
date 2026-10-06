"""
Interactive Google OAuth2 Authenticator and Latest Email Reader for Gmail.
Uses InstalledAppFlow to grant access and fetch the top 5 latest messages from inbox.
"""

import sys
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GmailOAuth2")

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError as e:
    logger.error(f"Missing required Google libraries: {e}")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service():
    """
    Authenticates user via OAuth2 and returns Gmail API service.
    """
    creds = None
    token_path = "token.json"

    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")

    if not client_id or not client_secret:
        logger.error("GMAIL_CLIENT_ID or GMAIL_CLIENT_SECRET not found in .env")
        return None

    # Load existing tokens if present
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials, run interactive browser flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired OAuth token...")
            creds.refresh(Request())
        else:
            logger.info("Starting local OAuth2 browser login flow on port 8080...")
            client_config = {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [
                        "http://localhost:8080/",
                        "http://127.0.0.1:8080/",
                        "http://localhost:8080",
                        "http://127.0.0.1:8080"
                    ]
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=8080)

        # Save the credentials for next runs
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())
            logger.info(f"OAuth token saved locally at {token_path}")

    return build("gmail", "v1", credentials=creds)


def list_latest_emails(max_results=5):
    """
    Fetches and displays the top latest emails from the authorized inbox.
    """
    service = get_gmail_service()
    if not service:
        return

    logger.info(f"Fetching top {max_results} latest emails from Inbox...")
    results = service.users().messages().list(userId="me", maxResults=max_results, q="in:inbox").execute()
    messages = results.get("messages", [])

    if not messages:
        logger.info("No messages found in Inbox.")
        return

    print("\n==========================================")
    print(f"   ÚLTIMOS {len(messages)} E-MAILS DA SUA CAIXA DE ENTRADA")
    print("==========================================\n")

    for idx, msg in enumerate(messages, 1):
        msg_detail = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        headers = msg_detail.get("payload", {}).get("headers", [])

        subject = "Sem Assunto"
        from_sender = "Desconhecido"
        date = ""

        for h in headers:
            if h["name"].lower() == "subject":
                subject = h["value"]
            elif h["name"].lower() == "from":
                from_sender = h["value"]
            elif h["name"].lower() == "date":
                date = h["value"]

        snippet = msg_detail.get("snippet", "")
        logger.info(f"[{idx}] {subject} | De: {from_sender} | Data: {date}")
        logger.info(f"    Snippet: {snippet[:100]}...")


if __name__ == "__main__":
    list_latest_emails(5)
