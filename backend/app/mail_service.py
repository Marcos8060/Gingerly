from flask import current_app
from flask_mail import Message
from app import mail


def deliver_email(recipient_name: str, recipient_email: str, subject: str, body: str) -> str:
    if current_app.config.get("MAIL_SUPPRESS_SEND", True):
        print(f"[MAIL] To: {recipient_email} | Subject: {subject}")
        return "sent"

    try:
        msg = Message(
            subject=subject,
            recipients=[f"{recipient_name} <{recipient_email}>"],
            body=body,
        )
        mail.send(msg)
        return "sent"
    except Exception as e:
        current_app.logger.error(f"Mail delivery failed to {recipient_email}: {e}")
        return "failed"
