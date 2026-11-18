"""List your recent Telegram dialogs with their user/chat IDs.

Run:  .venv\\Scripts\\python.exe find_id.py
"""

import asyncio
import sys

from telethon import TelegramClient

from config import API_HASH, API_ID, SESSION_NAME


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        async for d in client.iter_dialogs(limit=100):
            kind = "bot" if getattr(d.entity, "bot", False) else (
                "group" if d.is_group else ("channel" if d.is_channel else "user")
            )
            print(f"{d.id} | {kind:7} | {d.name}")


if __name__ == "__main__":
    asyncio.run(main())
