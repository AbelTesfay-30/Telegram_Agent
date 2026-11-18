"""Minimal SQLite layer for managing whitelisted users.

Schema:
    users(user_id INTEGER PRIMARY KEY,
          is_active INTEGER NOT NULL DEFAULT 0,
          status    TEXT    NOT NULL DEFAULT 'pending')

`is_active=1` means the AI may reply to this user.
`status` is free-form metadata (e.g. 'approved', 'blocked', 'pending').
"""

import aiosqlite

from config import DB_PATH

# Table creation DDL, executed once at startup.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id   INTEGER PRIMARY KEY,
    is_active INTEGER NOT NULL DEFAULT 0,
    status    TEXT    NOT NULL DEFAULT 'pending'
);
"""


async def init_db() -> None:
    """Create the database file and table if they don't exist."""
    async with aiosqlite.connect(DB_PATH, timeout=30) as db:
        await db.execute(_SCHEMA)
        await db.commit()


async def is_user_allowed(user_id: int) -> bool:
    """Return True if the user is whitelisted for AI responses."""
    async with aiosqlite.connect(DB_PATH, timeout=30) as db:
        async with db.execute(
            "SELECT is_active FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
    return bool(row and row[0])


async def upsert_user(user_id: int, is_active: int, status: str = "pending") -> None:
    """Insert or update a user record."""
    async with aiosqlite.connect(DB_PATH, timeout=30) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, is_active, status)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                is_active = excluded.is_active,
                status    = excluded.status
            """,
            (user_id, is_active, status),
        )
        await db.commit()


async def get_all_users() -> list[tuple[int, int, str]]:
    """Return all user rows as (user_id, is_active, status) tuples."""
    async with aiosqlite.connect(DB_PATH, timeout=30) as db:
        async with db.execute("SELECT user_id, is_active, status FROM users") as cur:
            return await cur.fetchall()
