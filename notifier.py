"""Notifier: sends admin alerts via a standard Telegram Bot (Bot API).

Uses plain `requests` — no python-telegram-bot dependency needed. All calls
are wrapped in try/except so notification failures never break the userbot.
"""

import logging

import requests

from config import ADMIN_ID, NOTIFIER_BOT_TOKEN

logger = logging.getLogger(__name__)

BOT_API = f"https://api.telegram.org/bot{NOTIFIER_BOT_TOKEN}"
REQUEST_TIMEOUT = 10


def _post(method: str, payload: dict) -> bool:
    """POST to the Bot API. Returns True on success, False otherwise."""
    if not NOTIFIER_BOT_TOKEN:
        logger.warning("NOTIFIER_BOT_TOKEN not set — skipping notification")
        return False
    try:
        resp = requests.post(f"{BOT_API}/{method}", json=payload, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.warning("Notifier request failed (%s): %s", method, exc)
        return False


def notify_admin(text: str, silent: bool = True) -> None:
    """Send a message to the admin chat via the notifier bot.

    Args:
        text: message body (Telegram HTML/Markdown not parsed — keep it plain).
        silent: send without a notification sound (default True for summaries).
    """
    _post("sendMessage", {"chat_id": ADMIN_ID, "text": text, "disable_notification": silent})


def notify_interaction(sender: str, incoming: str, reply: str, user_id: int) -> None:
    """Convenience helper: send a formatted AI-interaction summary to the admin."""
    # Truncate long messages so alerts stay readable.
    def clip(s: str, n: int = 500) -> str:
        s = s.replace("\n", " ")
        return s if len(s) <= n else s[:n] + "…"

    notify_admin(
        f"🤖 AI auto-reply\n"
        f"From: {clip(sender)} (id: {user_id})\n"
        f"Them: {clip(incoming)}\n"
        f"Me:   {clip(reply)}"
    )


def notify_error(context: str) -> None:
    """Alert the admin that something failed."""
    notify_admin(f"⚠️ Userbot error:\n{context}", silent=False)
