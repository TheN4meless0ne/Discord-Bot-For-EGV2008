import time
import aiohttp
import discord
from discord.ext import tasks

import db
from utils import get_env_variable

TWITCH_CLIENT_ID = get_env_variable("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = get_env_variable("TWITCH_CLIENT_SECRET")

CHECK_INTERVAL = 600
TIMEOUT = aiohttp.ClientTimeout(total=30)

# Cached app access token
_token = None
_token_expires = 0


# Get a Twitch access token, reused until it is about to expire
async def get_access_token(session):
    global _token, _token_expires

    if _token and time.monotonic() < _token_expires:
        return _token

    data = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    async with session.post("https://id.twitch.tv/oauth2/token", data=data) as response:
        if response.status != 200:
            raise RuntimeError(f"Twitch token error: {response.status}")
        body = await response.json()

    _token = body["access_token"]
    _token_expires = time.monotonic() + body.get("expires_in", 3600) - 300
    return _token


# Live streams for the given logins, as {login: stream}. 100 logins per request
async def get_live_streams(logins):
    global _token
    live = {}

    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        headers = {
            "Client-ID": TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {await get_access_token(session)}"
        }

        for i in range(0, len(logins), 100):
            params = [("first", "100")] + [("user_login", login) for login in logins[i:i + 100]]

            async with session.get(
                "https://api.twitch.tv/helix/streams", headers=headers, params=params
            ) as response:
                if response.status == 401:
                    _token = None
                if response.status != 200:
                    raise RuntimeError(f"Twitch streams error: {response.status}")
                body = await response.json()

            for stream in body["data"]:
                live[stream["user_login"].lower()] = stream

    return live


# Text that mentions a role. The @everyone role can't be mentioned by ID
def role_text(role):
    return "@everyone" if role.is_default() else role.mention


# Announce new streams in one server
async def notify_guild(bot, config, live):
    guild = bot.get_guild(config["guild_id"])
    channel = guild and guild.get_channel(config["notif_channel_id"])
    if channel is None:
        return

    role = guild.get_role(config["alert_role_id"]) if config["alert_role_id"] else None
    role_mention = role_text(role) if role else ""
    allowed = discord.AllowedMentions.none()
    if role:
        allowed = discord.AllowedMentions(
            everyone=role.is_default(), users=False, roles=[role], replied_user=False
        )

    notified = await db.get_notified(bot.db, guild.id)

    for login in await db.list_watched(bot.db, guild.id):
        stream = live.get(login)
        if stream is None:
            continue

        # Same stream as last time, or announced before stream IDs were stored
        if login in notified and notified[login] in (None, stream["id"]):
            if notified[login] is None:
                await db.mark_notified(bot.db, guild.id, login, stream["id"])
            continue

        url = f"https://www.twitch.tv/{login}"
        if login == config["streamer_login"]:
            message = f"I'm now live on Twitch!! {url} {role_mention}"
        else:
            name = discord.utils.escape_markdown(stream.get("user_name") or login)
            message = f"{name} is now live! {url} {role_mention}"

        await channel.send(message.strip(), allowed_mentions=allowed)
        await db.mark_notified(bot.db, guild.id, login, stream["id"])


# Ask Twitch once for all servers, then announce per server
async def check_all_guilds(bot):
    logins = await db.all_watched_logins(bot.db)
    if not logins:
        return

    live = await get_live_streams(logins)
    print(f"Live users: {sorted(live)}")

    for config in await db.configured_guilds(bot.db):
        # One server failing must not stop the others
        try:
            await notify_guild(bot, config, live)
        except discord.HTTPException as e:
            print(f"Could not notify guild {config['guild_id']}: {e}")


@tasks.loop(seconds=CHECK_INTERVAL)
async def notify_when_live(bot):
    await bot.wait_until_ready()

    # A failed check is skipped, nobody is treated as offline
    try:
        await check_all_guilds(bot)
    except Exception as e:
        print(f"Twitch notifier error: {e}")
