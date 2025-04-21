import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
from time import sleep
import json
from utils import tokens, TWITCH_USERNAMES, STREAMER
from commands import commands_list

intents = discord.Intents.default()
intents.message_content = True  # Må aktiveres under Privileged Gateway Intents på https://discord.com/developers/applications/
bot = commands.Bot(command_prefix="/", intents=intents)

DISCORD_TOKEN = tokens["DISCORD_TOKEN"]
TWITCH_CLIENT_ID = tokens["TWITCH_CLIENT_ID"]
TWITCH_CLIENT_SECRET = tokens["TWITCH_CLIENT_SECRET"]
NOTIF_CHANNEL_ID = int(tokens["NOTIF_CHANNEL_ID"])
CHECK_INTERVAL = 60  # Sekunder mellom hver sjekk

async def get_twitch_access_token():
    """Fetch an access token from Twitch."""
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params) as response:
            data = await response.json()
            return data["access_token"]

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

async def notify_when_live():
    """Periodically check if Twitch users are live and send notifications."""
    access_token = await get_twitch_access_token()
    notified_users = set()  # Keep track of users already notified
    while True:
        try:
            live_users = await check_live_status(access_token, TWITCH_USERNAMES)
            channel = bot.get_channel(NOTIF_CHANNEL_ID)
            if channel:
                for user in live_users:
                    if user not in notified_users:
                        if user == STREAMER:
                            await channel.send(f"I'm now live on Twitch!! Come say hi!! https://www.twitch.tv/{user} @everyone")
                        else:
                            await channel.send(f"{user} is now live on Twitch!! Go check them out!! https://www.twitch.tv/{user} @everyone")
                        notified_users.add(user)
                # Remove users who are no longer live from the notified list
                notified_users = notified_users.intersection(live_users)
        except Exception as e:
            print(f"Error checking Twitch live status: {e}")
        await asyncio.sleep(CHECK_INTERVAL)


# Registrerer kommandene i commands.py og legger dem til i botten.
@bot.event
async def on_ready():
    for command in commands_list: # commands_list er en liste med alle kommandoene og ligger i commands.py
        bot.tree.add_command(command)
    bot.loop.create_task(notify_when_live())
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


@bot.event
async def on_message(message):
    """on_message kjøres når botten mottar en melding."""
    text = message.content
    user = message.author

    # Sjekker om meldingen er fra boten selv, for å unngå at den svarer på seg selv.
    if user == bot.user:
        return

# Det finnes flere ulike events man kan bruke til ulike formål,
# se https://discordpy.readthedocs.io/en/latest/api.html#event-reference


# Til slutt; kjør botten med token fra token.txt (med litt tips og feilsøking)
# Du kan ignorere dette.
if __name__ == '__main__':
    print('Starter botten.')
    try:
        bot.run(DISCORD_TOKEN)
    except discord.errors.PrivilegedIntentsRequired:
        print('OBS! Din bot mangler "Message Content Intent", legg til denne \n'
              'på https://discord.com/developers/applications/ (Under Privileged Gateway Intents)')
    except discord.errors.LoginFailure:
        print('Kunne ikke logge på botten, bruker du riktig token i token.txt?')
    except FileNotFoundError:
        print('Finner ikke token.txt, har du kjørt setup.py og limt inn din token?')
    finally:
        # Vent 5 sekunder før EventLoop lukkes, som gir en større og mindre lesbar feilmelding.
        sleep(5)
