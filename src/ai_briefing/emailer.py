from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr


def recipients_from_env() -> list[str]:
    return [address.strip() for address in os.environ.get("AI_BRIEFING_RECIPIENTS", "").split(",") if address.strip()]


def send(subject: str, html: str, text: str, recipients: list[str]) -> None:
    if not recipients:
        raise ValueError("没有收件人：请设置 AI_BRIEFING_RECIPIENTS 或由 Airflow 注入")
    required = ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD")
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise RuntimeError(f"缺少邮件运行环境变量：{', '.join(missing)}")
    port = int(os.environ.get("SMTP_PORT", "587"))
    sender = os.environ.get("SMTP_FROM", os.environ["SMTP_USER"])
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr(("Daily AI Intelligence", sender))
    message["To"] = sender
    # BCC avoids exposing the internal distribution list in the message headers.
    message["Bcc"] = ", ".join(recipients)
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    smtp_class = smtplib.SMTP_SSL if port == 465 else smtplib.SMTP
    with smtp_class(os.environ["SMTP_HOST"], port, timeout=30) as server:
        if port != 465:
            server.starttls()
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        server.send_message(message)
    print(f"[sent] AI briefing to {len(recipients)} recipient(s)")

