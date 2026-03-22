"""
notify.py — Telegram notifications for etoir.ru lead form submissions.
"""
import json
import logging
import os
import urllib.request

logger = logging.getLogger(__name__)


def build_message(data: dict) -> str:
    """Format a human-readable notification text from a lead payload dict."""
    lines = [
        "📬 Новая заявка с etoir.ru",
        "",
        f"Имя: {data['name']}",
        f"Компания: {data['company']}",
        f"Телефон: {data['phone']}",
        f"Email: {data['email']}",
    ]
    if data.get("position"):
        lines.append(f"Должность: {data['position']}")
    if data.get("comment"):
        lines.append(f"Комментарий: {data['comment']}")
    return "\n".join(lines)


def send_telegram(text: str) -> None:
    """Send a plain-text message to the configured Telegram chat. Fire-and-forget."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        logger.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set, skipping notification")
        return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        body = json.dumps({"chat_id": chat_id, "text": text}, ensure_ascii=False).encode()
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as exc:
        logger.error("Failed to send Telegram notification: %s", exc)
