import discord
import asyncio
import aiohttp

from utils import (
    get_env_variable,
    get_twitch_access_token,
    load_twitch_usernames,
    STREAMER
)

NOTIF_CHANNEL_ID = int(get_env_variable("NOTIF_CHANNEL_ID"))
GUILD_ID = int(get_env_variable("GUILD_ID"))

TWITCH_CLIENT_ID = get_env_variable("TWITCH_CLIENT_ID")
TWITCH_USERNAMES = load_twitch_usernames()

ROLE = "Wants Alerts"
CHECK_INTERVAL = 600

async def check_live_status(access_token, usernames):
    url = "https://api.twitch.tv/helix/streams"

    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }

    live_users = []

    async with aiohttp.ClientSession() as session:
        for username in usernames:
            params = {"user_login": username}

            async with session.get(url, headers=headers, params=params) as response:
                data = await response.json()

                if len(data.get("data", [])) > 0:
                    live_users.append(username)

    return live_users

async def notify_when_live(bot):
    print("Twitch notifier started")

    notified_users = set()

    while True:
        try:
            access_token = await get_twitch_access_token()

            guild = bot.get_guild(GUILD_ID)
            if not guild:
                print("Guild not found, retrying...")
                await asyncio.sleep(10)
                continue

            role = discord.utils.get(guild.roles, name=ROLE)
            role_mention = role.mention if role else ""

            channel = bot.get_channel(NOTIF_CHANNEL_ID)

            live_users = await check_live_status(access_token, TWITCH_USERNAMES)
            print(f"Live users: {live_users}")

            if channel:
                for user in live_users:
                    if user not in notified_users:
                        if user == STREAMER:
                            await channel.send(
                                f"I'm now live on Twitch!! https://www.twitch.tv/{user} {role_mention}"
                            )
                        else:
                            await channel.send(
                                f"{user} is now live! https://www.twitch.tv/{user} {role_mention}"
                            )

                        notified_users.add(user)

                notified_users = notified_users.intersection(live_users)

        except Exception as e:
            print(f"Twitch notifier error: {e}")

        await asyncio.sleep(CHECK_INTERVAL)
