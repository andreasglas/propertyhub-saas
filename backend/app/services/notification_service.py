from __future__ import annotations

import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from typing import Literal

from app.config import get_settings


class NotificationService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def has_email_delivery(self) -> bool:
        return bool(self.settings.smtp_host and self.settings.smtp_from_email)

    def build_setup_url(self, invitation_token: str) -> str:
        return (
            self.settings.frontend_app_url.rstrip("/")
            + "/setup-password?token="
            + invitation_token
        )

    def _build_message(
        self, *, recipient_email: str, subject: str, text_content: str
    ) -> EmailMessage:
        message = EmailMessage()
        message["Subject"] = subject
        message["To"] = recipient_email
        message["From"] = formataddr(
            (self.settings.smtp_from_name, self.settings.smtp_from_email or "")
        )
        message.set_content(text_content)
        return message

    def _send_message(self, message: EmailMessage) -> None:
        if not self.has_email_delivery():
            raise RuntimeError("SMTP delivery is not configured")

        if self.settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(
                self.settings.smtp_host,
                self.settings.smtp_port,
                timeout=self.settings.smtp_timeout_seconds,
            ) as smtp:
                self._authenticate_and_send(smtp, message)
            return

        with smtplib.SMTP(
            self.settings.smtp_host,
            self.settings.smtp_port,
            timeout=self.settings.smtp_timeout_seconds,
        ) as smtp:
            if self.settings.smtp_use_tls:
                smtp.starttls()
            self._authenticate_and_send(smtp, message)

    def _authenticate_and_send(self, smtp: smtplib.SMTP, message: EmailMessage) -> None:
        if self.settings.smtp_username:
            smtp.login(
                self.settings.smtp_username,
                self.settings.smtp_password.get_secret_value()
                if self.settings.smtp_password is not None
                else "",
            )
        smtp.send_message(message)

    def send_user_invitation(
        self,
        *,
        recipient_email: str,
        recipient_name: str | None,
        organization_name: str,
        role: str,
        setup_url: str,
    ) -> Literal["manual", "sent"]:
        if not self.has_email_delivery():
            return "manual"

        greeting = recipient_name or recipient_email
        subject = f"Einladung zu {organization_name} in PropertyHub"
        body = (
            f"Hallo {greeting},\n\n"
            f"du wurdest als {role} zu {organization_name} eingeladen.\n"
            f"Richte dein Passwort hier ein:\n{setup_url}\n\n"
            "Viele Grüße\n"
            "PropertyHub"
        )
        message = self._build_message(
            recipient_email=recipient_email,
            subject=subject,
            text_content=body,
        )
        self._send_message(message)
        return "sent"

    def send_payment_reminder(
        self,
        *,
        recipient_email: str,
        organization_name: str,
        invoice_label: str,
        gross_amount: float,
        due_date: str | None,
        reminder_level: int,
        note: str | None,
    ) -> Literal["manual", "sent"]:
        if not self.has_email_delivery():
            return "manual"

        subject = f"Zahlungserinnerung Stufe {reminder_level} – {organization_name}"
        lines = [
            f"Hallo,",
            "",
            f"für {invoice_label} ist noch ein offener Betrag von {gross_amount:.2f} EUR vermerkt.",
        ]
        if due_date:
            lines.append(f"Fälligkeitsdatum: {due_date}")
        if note:
            lines.extend(["", f"Hinweis: {note}"])
        lines.extend(["", "Bitte prüfe den offenen Posten.", "", organization_name])
        message = self._build_message(
            recipient_email=recipient_email,
            subject=subject,
            text_content="\n".join(lines),
        )
        self._send_message(message)
        return "sent"
