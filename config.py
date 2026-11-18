"""Configuration for the personal Telegram Userbot.

All secrets are loaded from environment variables. Copy `.env.example`
to `.env` and fill in the values, or export them in your shell.
Never commit real secrets to version control.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root if present
load_dotenv(Path(__file__).resolve().parent / ".env")

# --- MTProto credentials (from https://my.telegram.org) ---
API_ID: int = int(os.getenv("API_ID", "0"))
API_HASH: str = os.getenv("API_HASH", "")

# --- Telethon session ---
SESSION_NAME: str = os.getenv("SESSION_NAME", "userbot")

# --- Google Gemini ---
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# --- Notifier bot (separate standard Telegram bot for admin alerts) ---
NOTIFIER_BOT_TOKEN: str = os.getenv("NOTIFIER_BOT_TOKEN", "")
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))

# --- Behaviour tuning ---
DB_PATH: str = os.getenv("DB_PATH", "userbot.db")
TYPING_DELAY_SECONDS: float = float(os.getenv("TYPING_DELAY_SECONDS", "1.5"))
CONTEXT_MESSAGE_COUNT: int = int(os.getenv("CONTEXT_MESSAGE_COUNT", "5"))

# --- System prompt template ---
# Placeholders: {name} = sender display name, {username} = sender username
SYSTEM_PROMPT: str = os.getenv(
    "SYSTEM_PROMPT",
    (
        "You are {name} (@{username}), responding personally on Telegram. "
        "Keep replies short, casual, and human-like — like a real text message, "
        "not an essay. Do not reveal that you are an AI."
    ),
)


def validate() -> list[str]:
    """Return a list of missing/invalid required settings."""
    problems: list[str] = []
    if not API_ID:
        problems.append("API_ID is missing or zero")
    if not API_HASH:
        problems.append("API_HASH is missing")
    if not GEMINI_API_KEY:
        problems.append("GEMINI_API_KEY is missing")
    if not NOTIFIER_BOT_TOKEN:
        problems.append("NOTIFIER_BOT_TOKEN is missing")
    if not ADMIN_ID:
        problems.append("ADMIN_ID is missing or zero")
    return problems
