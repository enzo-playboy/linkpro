"""
Telegram Notification Service for JobAutomator AI.
Sends real-time alerts to the candidate's Telegram bot when recruiters respond to applications.
"""

import sys
import os
import json
import logging
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TelegramNotifier")


class TelegramNotificationService:
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")

    def send_recruiter_alert(
        self,
        company_name: str,
        job_title: str,
        classification: str,
        summary: str,
        action_link: Optional[str] = None
    ) -> bool:
        """
        Formats and sends a high-priority Telegram message when a recruiter responds.
        """
        if not self.bot_token or not self.chat_id:
            logger.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Simulating notification locally...")
            logger.info(f"ALERT -> Empresa: {company_name} | Vaga: {job_title} | Status: {classification} | Resumo: {summary}")
            return False

        # Formatting Telegram message using Markdown
        emoji_map = {
            "INTERVIEW_INVITE": "🚨 *CONVITE PARA ENTREVISTA / TESTE!*",
            "STATUS_UPDATE": "ℹ️ *Atualização de Processo Seletivo*",
            "REJECTION": "📩 *Agradecimento / Feedback*"
        }
        header = emoji_map.get(classification, "📩 *Resposta de Vaga*")

        message_text = (
            f"{header}\n\n"
            f"🏢 *Empresa*: {company_name}\n"
            f"💼 *Vaga*: {job_title}\n\n"
            f"📝 *Resumo do E-mail*:\n{summary}\n"
        )
        if action_link:
            message_text += f"\n🔗 [Acessar Link do E-mail/Agendamento]({action_link})"

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message_text,
            "parse_mode": "Markdown"
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as resp:
                if resp.status == 200:
                    logger.info("Telegram alert successfully dispatched.")
                    return True
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")

        return False


def main():
    logger.info("Testing TelegramNotificationService...")
    notifier = TelegramNotificationService()

    # Sample alert test
    notifier.send_recruiter_alert(
        company_name="Tech Global Corp",
        job_title="Estágio em Desenvolvimento Java / IA",
        classification="INTERVIEW_INVITE",
        summary="Parabéns! Seu perfil foi selecionado para a etapa de entrevista técnica. Favor agendar seu horário.",
        action_link="https://calendly.com/techglobal-interview"
    )


if __name__ == "__main__":
    main()
