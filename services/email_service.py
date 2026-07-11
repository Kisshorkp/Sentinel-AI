"""SMTP email delivery."""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from config.settings import AppSettings


class EmailService:
    def __init__(self, settings: AppSettings):
        self.settings = settings

    def send(
        self,
        recipients: list[str],
        subject: str,
        body: str,
        *,
        html_body: str | None = None,
    ) -> None:
        if not recipients:
            raise ValueError("No recipients provided.")

        from_addr = self.settings.alert_from_email or self.settings.smtp_user
        from_name = (self.settings.alert_from_name or "").strip()
        from_header = formataddr((from_name, from_addr)) if from_name else from_addr

        if html_body:
            msg: MIMEMultipart | MIMEText = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_header
            msg["To"] = ", ".join(recipients)
            msg.attach(MIMEText(body, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))
        else:
            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = from_header
            msg["To"] = ", ".join(recipients)

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=30) as server:
            if self.settings.smtp_use_tls:
                server.starttls()
            server.login(self.settings.smtp_user, self.settings.smtp_password)
            server.sendmail(from_addr, recipients, msg.as_string())


def verify_smtp_login(settings: AppSettings) -> str | None:
    """Return an error message if SMTP login fails, else None."""
    if not settings.smtp_configured:
        return "SMTP not configured — set SMTP_HOST, SMTP_USER, and SMTP_PASSWORD in .env"
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            if settings.smtp_use_tls:
                server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
        return None
    except smtplib.SMTPAuthenticationError:
        return (
            "Gmail rejected the SMTP password. Create a new App Password at "
            "https://myaccount.google.com/apppasswords and update SMTP_PASSWORD in .env"
        )
    except Exception as exc:
        return f"SMTP connection failed: {exc}"
