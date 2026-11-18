"""One-off: send a greeting DM to every whitelisted (is_active=1) user.

Run:  .venv\\Scripts\\python.exe greet.py
"""

import asyncio

from telethon import TelegramClient
from telethon.errors import UserNotMutualContactError, UserPrivacyRestrictedError

import database
from config import API_HASH, API_ID, SESSION_NAME

GREETING = (
    "Hello! This is Bereket. I'm currently unavailable, but my assistant "
    "will be replying to your messages shortly. How may I help you today?"
)


async def main() -> None:
    users = await database.get_all_users()
    targets = [uid for uid, active, _ in users if active]
    if not targets:
        print("No whitelisted users found.")
        return

    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        for uid in targets:
            try:
                entity = await client.get_entity(uid)
                await client.send_message(entity, GREETING)
                name = getattr(entity, "first_name", str(uid))
                print(f"Sent to {name} ({uid})")
            except (UserNotMutualContactError, UserPrivacyRestrictedError) as exc:
                print(f"Skipped {uid}: privacy settings block DMs ({exc.__class__.__name__})")
            except Exception as exc:
                print(f"Failed {uid}: {exc}")
            # Be polite to Telegram's rate limits.
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
