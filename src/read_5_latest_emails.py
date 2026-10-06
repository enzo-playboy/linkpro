"""
Fetches and displays the 5 most recent emails from Gmail inbox.
"""

import os
import sys
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER", "yttoshiro444@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "gtkdaxuayqsgkmda")


def sanitize(text: str) -> str:
    if not text:
        return ""
    # Replaces common non-ascii characters for clean console output
    return text.encode('ascii', errors='ignore').decode('ascii')


def read_top_5_emails():
    print(f"Conectando ao Gmail ({GMAIL_USER})...")
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    mail.select("inbox")

    # Fetch ALL message IDs in inbox
    status, messages = mail.search(None, "ALL")
    if status != "OK" or not messages[0]:
        print("Nenhum e-mail encontrado na caixa de entrada.")
        return

    email_ids = messages[0].split()
    total = len(email_ids)
    print(f"Total de e-mails na caixa de entrada: {total}")

    # Get last 5 email IDs
    latest_5 = email_ids[-5:]
    latest_5.reverse() # Most recent first

    print("\n=======================================================")
    print("      OS 5 ULTIMOS E-MAILS DA SUA CAIXA DE ENTRADA")
    print("=======================================================\n")

    for idx, e_id in enumerate(latest_5, 1):
        res, msg_data = mail.fetch(e_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                # Decode Subject
                subject = "Sem Assunto"
                if msg["Subject"]:
                    subject_header = decode_header(msg["Subject"])[0]
                    subject = subject_header[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(subject_header[1] or "utf-8", errors="ignore")

                # Decode From
                from_sender = msg.get("From", "Desconhecido")

                # Date
                date = msg.get("Date", "")

                # Body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                            except Exception:
                                pass
                            break
                else:
                    try:
                        body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                    except Exception:
                        pass

                body_snippet = " ".join(body.split())[:180]

                print(f"[{idx}] ASSUNTO: {subject}")
                print(f"    DE: {from_sender}")
                print(f"    DATA: {date}")
                print(f"    RESUMO: {body_snippet}...")
                print("-" * 55 + "\n")

    mail.logout()


if __name__ == "__main__":
    read_top_5_emails()
