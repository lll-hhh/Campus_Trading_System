"""Notification utilities (email alerts, etc.)."""
from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Iterable

from loguru import logger

from apps.core.config import get_settings


class EmailNotificationService:
    """Simple SMTP-based notification helper."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def _build_message(self, subject: str, body: str, recipients: Iterable[str]) -> EmailMessage:
        message = EmailMessage()
        sender = self.settings.alert_sender or (self.settings.smtp_username or "noreply@campuswap")
        message["Subject"] = subject
        message["From"] = sender
        message["To"] = ", ".join(recipients)
        message.set_content(body)
        return message

    def send(self, subject: str, body: str) -> None:
        """Send an email using configured SMTP credentials (best effort)."""

        recipients = self.settings.alert_recipients
        if not recipients:
            logger.warning("Skipping email notification - no recipients configured")
            return
        if not self.settings.smtp_host:
            logger.warning("Skipping email notification - SMTP host not configured")
            return

        message = self._build_message(subject, body, recipients)
        try:
            if self.settings.smtp_use_tls:
                with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as smtp:
                    smtp.starttls()
                    if self.settings.smtp_username and self.settings.smtp_password:
                        smtp.login(self.settings.smtp_username, self.settings.smtp_password)
                    smtp.send_message(message)
            else:
                with smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port) as smtp:
                    if self.settings.smtp_username and self.settings.smtp_password:
                        smtp.login(self.settings.smtp_username, self.settings.smtp_password)
                    smtp.send_message(message)
            logger.info("Email notification sent", subject=subject, recipients=recipients)
        except Exception as exc:  # pragma: no cover - best effort
            logger.exception("Failed to send email notification", error=str(exc))


email_notifier = EmailNotificationService()
