# SQLite database for per-server config. All SQL lives here.
import json
import os

import aiosqlite

DATABASE_PATH = os.getenv("DATABASE_PATH", "/data/bot.sqlite3")

SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS guild_config (
    guild_id           INTEGER PRIMARY KEY,
    notif_channel_id   INTEGER,
    socials_channel_id INTEGER,
    alert_role_id      INTEGER,
    streamer_login     TEXT
);

CREATE TABLE IF NOT EXISTS watched (
    guild_id     INTEGER NOT NULL REFERENCES guild_config(guild_id) ON DELETE CASCADE,
    twitch_login TEXT    NOT NULL,
    PRIMARY KEY (guild_id, twitch_login)
);

-- Already announced as live
CREATE TABLE IF NOT EXISTS notified (
    guild_id     INTEGER NOT NULL REFERENCES guild_config(guild_id) ON DELETE CASCADE,
    twitch_login TEXT    NOT NULL,
    PRIMARY KEY (guild_id, twitch_login)
);
"""


# Open the database and create or update the tables
async def connect(path: str = DATABASE_PATH) -> aiosqlite.Connection:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    conn = await aiosqlite.connect(path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode = WAL")
    await conn.execute("PRAGMA foreign_keys = ON")
    await _migrate(conn)
    return conn


# Schema version is stored in PRAGMA user_version
async def _migrate(conn: aiosqlite.Connection) -> None:
    async with conn.execute("PRAGMA user_version") as cur:
        (version,) = await cur.fetchone()

    if version < 1:
        await conn.executescript(SCHEMA_V1)
        version = 1

    # Add new schema versions here (if version < 2: ...)

    await conn.execute(f"PRAGMA user_version = {version}")
    await conn.commit()


# Twitch logins are case-insensitive, store them lower-case
def _normalise(login: str) -> str:
    return login.strip().lower()


# Config row for a server, or None
async def get_guild_config(conn, guild_id: int):
    async with conn.execute(
        "SELECT * FROM guild_config WHERE guild_id = ?", (guild_id,)
    ) as cur:
        return await cur.fetchone()


# Create the server's row if missing, then update the given fields
async def upsert_guild_config(conn, guild_id: int, **fields) -> None:
    allowed = {"notif_channel_id", "socials_channel_id", "alert_role_id", "streamer_login"}
    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"Unknown guild_config fields: {unknown}")

    await conn.execute(
        "INSERT OR IGNORE INTO guild_config (guild_id) VALUES (?)", (guild_id,)
    )
    if fields:
        assignments = ", ".join(f"{name} = ?" for name in fields)
        await conn.execute(
            f"UPDATE guild_config SET {assignments} WHERE guild_id = ?",
            (*fields.values(), guild_id),
        )
    await conn.commit()


# Remove everything for a server
async def delete_guild(conn, guild_id: int) -> None:
    await conn.execute("DELETE FROM guild_config WHERE guild_id = ?", (guild_id,))
    await conn.commit()


# Servers with a notification channel set
async def configured_guilds(conn):
    async with conn.execute(
        "SELECT * FROM guild_config WHERE notif_channel_id IS NOT NULL"
    ) as cur:
        return await cur.fetchall()


# Add a Twitch login. Returns False if already watched
async def add_watched(conn, guild_id: int, login: str) -> bool:
    await upsert_guild_config(conn, guild_id)
    cur = await conn.execute(
        "INSERT OR IGNORE INTO watched (guild_id, twitch_login) VALUES (?, ?)",
        (guild_id, _normalise(login)),
    )
    await conn.commit()
    return cur.rowcount == 1


# Remove a Twitch login. Returns False if not watched
async def remove_watched(conn, guild_id: int, login: str) -> bool:
    login = _normalise(login)
    cur = await conn.execute(
        "DELETE FROM watched WHERE guild_id = ? AND twitch_login = ?",
        (guild_id, login),
    )
    await conn.execute(
        "DELETE FROM notified WHERE guild_id = ? AND twitch_login = ?",
        (guild_id, login),
    )
    await conn.commit()
    return cur.rowcount == 1


# Twitch logins watched by a server
async def list_watched(conn, guild_id: int) -> list[str]:
    async with conn.execute(
        "SELECT twitch_login FROM watched WHERE guild_id = ? ORDER BY twitch_login",
        (guild_id,),
    ) as cur:
        return [row["twitch_login"] for row in await cur.fetchall()]


# Unique Twitch logins across all servers
async def all_watched_logins(conn) -> list[str]:
    async with conn.execute(
        "SELECT DISTINCT twitch_login FROM watched"
    ) as cur:
        return [row["twitch_login"] for row in await cur.fetchall()]


# Logins already announced in a server
async def get_notified(conn, guild_id: int) -> set[str]:
    async with conn.execute(
        "SELECT twitch_login FROM notified WHERE guild_id = ?", (guild_id,)
    ) as cur:
        return {row["twitch_login"] for row in await cur.fetchall()}


# Replace the announced logins with whoever is live now
async def set_notified(conn, guild_id: int, live_logins: set[str]) -> None:
    await conn.execute("DELETE FROM notified WHERE guild_id = ?", (guild_id,))
    await conn.executemany(
        "INSERT INTO notified (guild_id, twitch_login) VALUES (?, ?)",
        [(guild_id, login) for login in live_logins],
    )
    await conn.commit()


# Import the old env vars and twitch_usernames.json for the original server.
# Skipped if the server already has a row. Returns True if imported
async def import_legacy_config(conn, guild_id: int, notif_channel_id, socials_channel_id,
                               streamer_login: str, usernames_files: list[str]) -> bool:
    if await get_guild_config(conn, guild_id) is not None:
        return False

    usernames = []
    for path in usernames_files:
        try:
            with open(path, "r") as file:
                usernames = json.load(file)
            break
        except FileNotFoundError:
            continue

    await conn.execute(
        """INSERT INTO guild_config
           (guild_id, notif_channel_id, socials_channel_id, streamer_login)
           VALUES (?, ?, ?, ?)""",
        (guild_id, notif_channel_id, socials_channel_id, _normalise(streamer_login)),
    )
    await conn.executemany(
        "INSERT OR IGNORE INTO watched (guild_id, twitch_login) VALUES (?, ?)",
        [(guild_id, _normalise(name)) for name in usernames],
    )
    await conn.commit()
    return True
