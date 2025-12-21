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

    def _build_message(
        self,
        subject: str,
        body: str,
        recipients: Iterable[str],
        sender: str | None = None,
    ) -> EmailMessage:
        message = EmailMessage()
        sender_email = sender or self.settings.alert_sender or (self.settings.smtp_username or "noreply@campuswap")
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = ", ".join(recipients)
        message.set_content(body)
        return message

    def send(self, subject: str, body: str) -> None:
        """Send an email using configured SMTP credentials (best effort)."""

        runtime = self._load_runtime_email_settings()

        smtp_host = runtime.get("smtp_server") or self.settings.smtp_host
        smtp_port = runtime.get("smtp_port") or self.settings.smtp_port
        smtp_username = runtime.get("smtp_username") or self.settings.smtp_username
        smtp_password = runtime.get("smtp_password") or self.settings.smtp_password
        use_tls = runtime.get("use_tls") if runtime.get("use_tls") is not None else self.settings.smtp_use_tls
        sender = runtime.get("from_email") or self.settings.alert_sender
        recipients = runtime.get("admin_emails") or self.settings.alert_recipients

        if not recipients:
            logger.warning("Skipping email notification - no recipients configured")
            return
        if not smtp_host:
            logger.warning("Skipping email notification - SMTP host not configured")
            return

        message = self._build_message(subject, body, recipients, sender=sender)
        try:
            if use_tls:
                with smtplib.SMTP(smtp_host, smtp_port) as smtp:
                    smtp.starttls()
                    if smtp_username and smtp_password:
                        smtp.login(smtp_username, smtp_password)
                    smtp.send_message(message)
            else:
                with smtplib.SMTP_SSL(smtp_host, smtp_port) as smtp:
                    if smtp_username and smtp_password:
                        smtp.login(smtp_username, smtp_password)
                    smtp.send_message(message)
            logger.info("Email notification sent", subject=subject, recipients=recipients)
        except Exception as exc:  # pragma: no cover - best effort
            logger.exception("Failed to send email notification", error=str(exc))

    def _load_runtime_email_settings(self) -> dict:
        """Load overrides stored via admin System Settings if available."""

        try:
            from apps.core.database import db_manager
            from apps.core.models import SystemSetting

            with db_manager.session_scope("mysql") as session:
                row = (
                    session.query(SystemSetting)
                    .filter(SystemSetting.category == "notification", SystemSetting.key == "email")
                    .one_or_none()
                )
                if row and isinstance(row.value, dict):
                    return row.value
        except Exception as exc:  # pragma: no cover - best effort
            logger.debug("Runtime email settings unavailable: %s", exc)
        return {}


email_notifier = EmailNotificationService()
