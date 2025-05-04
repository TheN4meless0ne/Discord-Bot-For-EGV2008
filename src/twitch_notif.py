import discord
from discord import app_commands
import aiohttp
import asyncio
from utils import tokens, TWITCH_USERNAMES, STREAMER, TWITCH_CLIENT_ID
from utils import get_twitch_access_token

NOTIF_CHANNEL_ID = int(tokens["NOTIF_CHANNEL_ID"])
GUILD_ID = int(tokens["GUILD_ID"])
ROLE = "Wants Alerts"
CHECK_INTERVAL = 60  # Sekunder mellom hver sjekk

async def check_live_status(access_token, usernames):
    """Check if any Twitch users are live."""
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
                if len(data["data"]) > 0: # User is live
                    live_users.append(username)
    return live_users

async def notify_when_live(bot):
    """Periodically check if Twitch users are live and send notifications."""
    access_token = await get_twitch_access_token()
    notified_users = set()  # Keep track of users already notified
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        print(f"Could not find guild with ID {GUILD_ID}")
        return
    role = discord.utils.get(guild.roles, name=ROLE)
    while True:
        try:
            live_users = await check_live_status(access_token, TWITCH_USERNAMES)
            channel = bot.get_channel(NOTIF_CHANNEL_ID)
            if channel:
                for user in live_users:
                    if user not in notified_users:
                        if user == STREAMER:
                            await channel.send(f"I'm now live on Twitch!! Come say hi!! https://www.twitch.tv/{user} {role.mention}")
                        else:
                            await channel.send(f"{user} is now live on Twitch!! Go check them out!! https://www.twitch.tv/{user} {role.mention}")
                        notified_users.add(user)
                # Remove users who are no longer live from the notified list
                notified_users = notified_users.intersection(live_users)
        except Exception as e:
            print(f"Error checking Twitch live status: {e}")
        await asyncio.sleep(CHECK_INTERVAL)