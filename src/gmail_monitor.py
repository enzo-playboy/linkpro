"""
Gmail Monitor & Email Classifier for JobAutomator AI.
Monitors candidate inbox for recruiter responses and triggers Telegram notifications.
Optimized for high-volume inboxes (processes top 30 most recent unread messages).
"""

import sys
import os
import json
import logging
import imaplib
import email
from email.header import decode_header
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from telegram_notifier import TelegramNotificationService

# Load .env variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GmailMonitor")


class GmailMonitorService:
    def __init__(self):
        self.email_address = os.getenv("GMAIL_USER", "")
        self.app_password = os.getenv("GMAIL_APP_PASSWORD", "")
        self.notifier = TelegramNotificationService()

    def check_unread_recruiter_emails(self, max_recent: int = 30) -> List[Dict[str, Any]]:
        """
        Connects to Gmail IMAP securely, fetches recent unread emails, and checks for recruiter keywords.
        """
        if not self.email_address or not self.app_password:
            logger.warning("GMAIL_USER or GMAIL_APP_PASSWORD not set in .env. Running simulation mode.")
            return self._simulate_incoming_emails()

        results = []
        try:
            logger.info(f"Connecting to Gmail IMAP for user {self.email_address}...")
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.email_address, self.app_password)
            mail.select("inbox")

            status, messages = mail.search(None, "UNSEEN")
            if status != "OK" or not messages[0]:
                logger.info("No unread messages found in inbox.")
                return results

            email_ids = messages[0].split()
            total_unread = len(email_ids)
            # Take the top N most recent unread email IDs
            recent_ids = email_ids[-max_recent:]
            logger.info(f"Total unread in inbox: {total_unread}. Analyzing top {len(recent_ids)} most recent messages...")

            for e_id in recent_ids:
                res, msg_data = mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject, encoding = decode_header(msg["Subject"])[0] if msg["Subject"] else ("Sem Assunto", None)
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding or "utf-8", errors="ignore")
                        from_sender = msg.get("From", "")

                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                        classification, summary = self._classify_email_content(from_sender, subject, body)
                        if classification != "IRRELEVANT":
                            item = {
                                "company": from_sender,
                                "subject": subject,
                                "classification": classification,
                                "summary": summary
                            }
                            results.append(item)
                            logger.info(f"RECRUITER ALERT DETECTED: {item['subject']} from {item['company']}")
                            self.notifier.send_recruiter_alert(
                                company_name=item["company"],
                                job_title=item["subject"],
                                classification=item["classification"],
                                summary=item["summary"]
                            )

            mail.logout()
        except Exception as e:
            logger.error(f"Error accessing Gmail via IMAP: {e}")

        return results

    def _classify_email_content(self, from_sender: str, subject: str, body: str) -> (str, str):
        """
        Classifies incoming email based on recruiter keywords or filters system emails.
        """
        text = (subject + " " + body).lower()
        sender_lower = from_sender.lower()

        # System / Automated noise filter
        ignored_senders = [
            "no-reply@accounts.google.com", "notifications@google.com", "noreply@google.com",
            "support@google.com", "no-reply@youtube.com", "info@twitter.com"
        ]
        if any(ign in sender_lower for ign in ignored_senders):
            return "IRRELEVANT", ""

        keywords_interview = [
            "entrevista", "interview", "teste técnico", "teste prático", "agendamento",
            "processo seletivo", "gostaríamos de agendar", "parabéns", "convite para",
            "recrutamento", "vaga de estágio", "gupy", "lever", "greenhouse"
        ]
        keywords_update = ["status da sua candidatura", "atualização do processo", "recebemos sua candidatura"]

        if any(kw in text for kw in keywords_interview):
            return "INTERVIEW_INVITE", f"E-mail de recrutamento referente a '{subject}'. Convite ou etapa do processo seletivo detectada."
        elif any(kw in text for kw in keywords_update):
            return "STATUS_UPDATE", f"Atualização de processo seletivo: '{subject}'."
        
        return "IRRELEVANT", ""

    def _simulate_incoming_emails(self) -> List[Dict[str, Any]]:
        sample_alerts = [
            {
                "company": "Recrutamento Tech Corp",
                "subject": "Convite para Entrevista Técnica - Estágio Java",
                "classification": "INTERVIEW_INVITE",
                "summary": "Prezado candidato, gostamos do seu currículo e gostaríamos de agendar a primeira conversa técnica."
            }
        ]
        for alert in sample_alerts:
            self.notifier.send_recruiter_alert(
                company_name=alert["company"],
                job_title=alert["subject"],
                classification=alert["classification"],
                summary=alert["summary"]
            )
        return sample_alerts


def main():
    logger.info("Running GmailMonitorService with active Gmail account...")
    monitor = GmailMonitorService()
    results = monitor.check_unread_recruiter_emails(max_recent=30)
    print(f"\n--- Leitura Real do Gmail Concluída: {len(results)} alerta(s) de recrutadores encontrados ---")


if __name__ == "__main__":
    main()
