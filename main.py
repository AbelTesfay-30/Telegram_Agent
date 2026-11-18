"""Main entrypoint: personal Telegram Userbot.

Workflow per incoming private DM:
    1. Ignore non-private chats and non-whitelisted users.
    2. Send a "typing..." action.
    3. Fetch last N messages for context.
    4. Generate a reply with Gemini.
    5. Send the reply via Telethon.
    6. Send a silent summary to the admin via the notifier bot.

First run will prompt for phone code and create a `.session` file —
run `python main.py` once locally to authenticate, then deploy.
"""

import asyncio
import logging
import sys

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

import database
import notifier
from ai_agent import AIAgent, AIError
from config import (
    API_HASH,
    API_ID,
    CONTEXT_MESSAGE_COUNT,
    SESSION_NAME,
    TYPING_DELAY_SECONDS,
    validate,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("userbot")

# One client for the whole app; reused across handlers.
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
# Initialized in main() after config validation — handlers only run
# after client.start(), so this is always set by the time it's used.
ai: AIAgent | None = None


@client.on(events.NewMessage)
async def handle_message(event: events.NewMessage.Event) -> None:
    """Handle every incoming message; filter down to actionable DMs."""
    try:
        msg = event.message

        # 1. Private chats only — skip groups, channels, broadcasts.
        if not event.is_private:
            return

        # Ignore our own outgoing messages and empty/service messages.
        if msg.out or not msg.raw_text:
            return

        sender = await event.get_sender()
        if sender is None:
            return
        user_id = sender.id

        # 2. Whitelist check.
        if not await database.is_user_allowed(user_id):
            logger.debug("Ignoring non-whitelisted user %s", user_id)
            return

        incoming_text = msg.raw_text
        sender_name = getattr(sender, "first_name", "") or "Unknown"
        if getattr(sender, "last_name", None):
            sender_name += f" {sender.last_name}"
        sender_username = getattr(sender, "username", "") or ""

        logger.info("DM from %s (%s): %s", sender_name, user_id, incoming_text[:80])

        # 3. Simulate human: show "typing..." briefly.
        async with client.action(event.chat_id, "typing"):
            await asyncio.sleep(TYPING_DELAY_SECONDS)

        # 4. Build context from the last N messages in this chat.
        context_lines: list[str] = []
        async for old in client.iter_messages(event.chat_id, limit=CONTEXT_MESSAGE_COUNT):
            if old.out:
                who = "Me"
            else:
                who = sender_name
            text = (old.raw_text or "").strip()
            if text:
                context_lines.append(f"{who}: {text}")
        context_lines.reverse()  # iter_messages returns newest-first

        # 5. Generate the reply.
        assert ai is not None  # set in main() before the client starts
        try:
            reply_text = await ai.generate(
                context=context_lines,
                sender_name=sender_name,
                sender_username=sender_username,
            )
        except AIError as exc:
            logger.error("AI generation failed for user %s: %s", user_id, exc)
            # requests is blocking — run it in a thread so the listener stays live.
            await asyncio.to_thread(
                notifier.notify_error, f"AI failed for {sender_name} ({user_id}): {exc}"
            )
            return  # don't reply with garbage; admin gets alerted

        # 6. Dispatch the reply.
        await client.send_message(event.chat_id, reply_text)
        logger.info("Replied to %s: %s", sender_name, reply_text[:80])

        # 7. Human-in-the-loop: silent admin summary.
        await asyncio.to_thread(
            notifier.notify_interaction, sender_name, incoming_text, reply_text, user_id
        )

    except FloodWaitError as exc:
        # Telegram rate-limited us — wait it out and retry later naturally.
        logger.warning("FloodWait: sleeping %ss", exc.seconds)
        await asyncio.sleep(min(exc.seconds, 60))
    except Exception as exc:
        # Catch-all so one bad message never kills the event loop.
        logger.exception("Unhandled error in message handler")
        await asyncio.to_thread(notifier.notify_error, f"Handler crash: {exc}")


async def main() -> None:
    """Validate config, init DB, connect, and run forever."""
    global ai

    problems = validate()
    if problems:
        for p in problems:
            logger.error("Config problem: %s", p)
        sys.exit(1)

    await database.init_db()
    ai = AIAgent()

    logger.info("Connecting to Telegram as user (session: %s)...", SESSION_NAME)
    await client.start()  # prompts for phone + code on first run
    me = await client.get_me()
    logger.info("Logged in as %s (id: %s)", me.first_name, me.id)

    logger.info("Userbot is running. Listening for whitelisted DMs...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down.")
