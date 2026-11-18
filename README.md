# Azahell Tech — AI-Powered Telegram Userbot

A production-grade personal Telegram automation agent built with Python.
It monitors private direct messages, generates contextual human-like replies
using Google Gemini, and reports every interaction to an administrator
through a separate Telegram notifier bot.

Designed for reliability, clean architecture, and responsible automation.

---

**Overview**
This project implements an autonomous messaging agent that operates on a
personal Telegram account via the MTProto protocol (Telethon). It is not a
conventional bot — it authenticates as a real user, simulates human typing
behavior, maintains conversation context, and produces AI-generated responses
that are indistinguishable from manual replies.

The system follows a strict human-in-the-loop model: every automated
interaction is silently logged to a private admin channel, giving the owner
full visibility and control over the agent's behavior.

**Key Features**
- Private DM monitoring with whitelist-based access control
- Human behavior simulation (typing indicators, response delays)
- Context-aware reply generation using the last 5 messages of a conversation
- Google Gemini integration with timeout and error resilience
- Asynchronous architecture — non-blocking I/O throughout
- SQLite persistence for user management (aiosqlite, fully async)
- Silent admin notifications via a dedicated Telegram Bot API integration
- Graceful handling of Telegram rate limits (FloodWait)
- Comprehensive error handling — the agent never crashes on AI failure
- Environment-based secret management (.env, git-ignored)

**How It Compares**
| Capability | Manual Replies | Standard Telegram Bot | This Userbot |
|---|---|---|---|
| Response speed | Hours or days | Instant | Seconds |
| Availability | Business hours only | 24/7 | 24/7 |
| Conversation context | Full human memory | Stateless or limited | Last N messages + persona prompt |
| Reply authenticity | Fully human | Obvious bot behavior | Human-like typing and tone |
| DM access | Personal account | Requires user to initiate | Reads existing private chats |
| Admin oversight | N/A | Bot logs | Silent per-message audit trail |
| Access control | Personal judgment | Command-based | SQLite whitelist per user |
| Failure resilience | N/A | Varies | AI errors isolated, admin alerted |

**Architecture**
```
Incoming DM
    |
    v
[Filter Layer]  -- ignores groups, channels, own messages,
    |              and non-whitelisted users
    v
[Typing Simulation]  -- "typing..." status + configurable delay
    |
    v
[Context Engine]  -- fetches last N messages for conversation history
    |
    v
[AI Generation]  -- Gemini API with system prompt, timeout,
    |               and safety-filter handling
    v
[Dispatch]  -- sends reply via Telethon
    |
    v
[Admin Notification]  -- silent summary to owner via Bot API
```

**Project Structure**
```
ABTG/
|-- main.py            Telethon client, event handlers, core workflow
|-- config.py          Environment configuration and validation
|-- database.py        Async SQLite layer for user whitelist management
|-- ai_agent.py        Gemini API wrapper with prompt engineering and error handling
|-- notifier.py        Telegram Bot API client for admin alerts
|-- greet.py           Utility: send greeting to whitelisted users
|-- find_id.py         Utility: list dialogs and resolve user IDs
|-- requirements.txt   Python dependencies
|-- .env.example       Configuration template (no secrets)
|-- .gitignore         Protects secrets, sessions, and databases
`-- README.md          This file
```

**Technology Stack**
| Component | Technology | Purpose |
|---|---|---|
| Language | Python 3.10+ | Core runtime |
| MTProto Client | Telethon 1.x | User account authentication and messaging |
| AI Engine | Google Gemini API | Contextual response generation |
| Database | SQLite + aiosqlite | Async user whitelist persistence |
| Notifications | Telegram Bot API (requests) | Admin alerts and interaction logs |
| Configuration | python-dotenv | Secret management via environment variables |

**Setup Guide**
**Prerequisites**
- Python 3.10 or higher
- A personal Telegram account
- A Google account (for Gemini API access)
- A Telegram account for the notifier bot (can be the same person)

**Step 1 — Install Dependencies**
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

**Step 2 — Obtain Credentials**
**Telegram API Credentials (MTProto)**
1. Visit https://my.telegram.org and sign in with your phone number.
2. Navigate to "API development tools" and create an application.
3. Record the `api_id` (integer) and `api_hash` (string).

**Google Gemini API Key**
1. Visit https://aistudio.google.com and sign in.
2. Select "Get API key" and create a new key.
3. The free tier is sufficient for development and light usage.

**Notifier Bot Token**
1. Open Telegram and message @BotFather.
2. Send `/newbot` and follow the prompts to create a bot.
3. Copy the bot token provided.
4. Open a chat with your new bot and press Start once — this is required
   before the bot can send you messages.
5. Retrieve your numeric user ID by messaging @userinfobot.

**Step 3 — Configure Environment**
```bash
cp .env.example .env
```

Edit `.env` and populate all required values:

| Variable | Description |
|---|---|
| `API_ID` | Telegram API ID from my.telegram.org |
| `API_HASH` | Telegram API hash from my.telegram.org |
| `GEMINI_API_KEY` | Google Gemini API key |
| `GEMINI_MODEL` | Model identifier (default: gemini-1.5-flash) |
| `NOTIFIER_BOT_TOKEN` | Token from @BotFather |
| `ADMIN_ID` | Your numeric Telegram user ID |

Optional tuning parameters (`TYPING_DELAY_SECONDS`,
`CONTEXT_MESSAGE_COUNT`, `SYSTEM_PROMPT`, `DB_PATH`) are documented
in `.env.example`.

**Step 4 — First Authentication**
```bash
python main.py
```

On first run, the agent prompts for your phone number, the login code
sent to your Telegram app, and your two-factor authentication password
if enabled. A `userbot.session` file is created — this file represents
your authenticated session and must be kept confidential and backed up.

Subsequent runs authenticate silently using the existing session file.

**Step 5 — Whitelist Users**
The agent ignores all users by default. To authorize a contact:

```bash
python -c "import asyncio; from database import upsert_user; asyncio.run(upsert_user(USER_ID, 1, 'approved'))"
```

To revoke access:

```bash
python -c "import asyncio; from database import upsert_user; asyncio.run(upsert_user(USER_ID, 0, 'blocked'))"
```

To list all registered users:

```bash
python -c "import asyncio; from database import get_all_users; print(asyncio.run(get_all_users()))"
```

To discover user IDs from existing conversations, run `find_id.py`:

```bash
python find_id.py
```

**Step 6 — Run the Agent**
```bash
python main.py
```

Expected console output on successful startup:

```
INFO | userbot | Connecting to Telegram as user (session: userbot)...
INFO | userbot | Logged in as <Your Name> (id: <your_id>)
INFO | userbot | Userbot is running. Listening for whitelisted DMs...
```

**Deployment**
**Windows (Persistent Background Process)**
Use Task Scheduler or a process manager such as NSSM to run the agent
as a Windows service:

```
Executable: C:\path\to\.venv\Scripts\python.exe
Arguments:  C:\path\to\ABTG\main.py
WorkingDir: C:\path\to\ABTG
```

**Linux VPS (systemd)**
Create `/etc/systemd/system/userbot.service`:

```ini
[Unit]
Description=Telegram AI Userbot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/ABTG
ExecStart=/opt/ABTG/.venv/bin/python main.py
Restart=always
RestartSec=5
User=youruser

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now userbot
sudo journalctl -u userbot -f
```

**Security Considerations**
- `.env`, `*.session`, and `*.db` files are excluded from version control
  via `.gitignore`. Never commit credentials or session files.
- The `userbot.session` file grants full access to the Telegram account.
  Treat it as a password: store it securely and never share it.
- All secrets are loaded exclusively from environment variables. No
  credentials are hardcoded anywhere in the source code.
- The notifier bot token and admin ID are validated at startup; missing
  configuration produces a clear error rather than a runtime failure.
- Rate limiting (FloodWait) is handled gracefully to protect the account
  from Telegram restrictions.

**Operational Notes**
- The agent responds only to whitelisted private messages. Group chats,
  channels, broadcast messages, and the account owner's own outgoing
  messages are ignored by design.
- Gemini API failures (rate limits, timeouts, safety filter blocks) are
  caught and reported to the admin without interrupting the listener.
- Database connections use a 30-second busy timeout to prevent lock
  contention under concurrent access.
- Notification delivery is non-blocking; a slow Bot API response does
  not freeze the Telegram event listener.

**Customization**
The agent's personality and behavior are controlled through environment
variables:

- `SYSTEM_PROMPT` — defines the persona the AI adopts. Supports
  `{name}` and `{username}` placeholders for personalization.
- `TYPING_DELAY_SECONDS` — duration of the simulated typing indicator.
- `CONTEXT_MESSAGE_COUNT` — number of historical messages provided
  as context to the AI (default: 5).
- `GEMINI_MODEL` — swap models as Google releases new versions.

**Disclaimer**
This software automates a personal Telegram account, which may conflict
with Telegram's Terms of Service in certain jurisdictions. Use responsibly
and at your own risk. The whitelist mechanism and human-in-the-loop
logging are provided specifically to keep automation transparent and
controlled.

**License**
Private project — All rights reserved.

---

Built by Azahell Tech
Contact: @AzahellNotifierbot (admin notifications)

