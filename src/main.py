import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
from time import sleep
import json

intents = discord.Intents.default()
intents.message_content = True  # Må aktiveres under Privileged Gateway Intents på https://discord.com/developers/applications/
bot = commands.Bot(command_prefix="/", intents=intents)

# Load tokens from token.txt
def load_tokens():
    tokens = {}
    with open("token.txt", "r") as file:
        for line in file:
            key, value = line.strip().split("=")
            tokens[key] = value
    return tokens

# Load Twitch usernames from a file
def load_twitch_usernames():
    try:
        with open("twitch_usernames.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return ["EGV2008", "nmlsval"]  # Default usernames if the file doesn't exist

# Save Twitch usernames to a file
def save_twitch_usernames(usernames):
    with open("twitch_usernames.json", "w") as file:
        json.dump(usernames, file)

tokens = load_tokens()
DISCORD_TOKEN = tokens["DISCORD_TOKEN"]
TWITCH_CLIENT_ID = tokens["TWITCH_CLIENT_ID"]
TWITCH_CLIENT_SECRET = tokens["TWITCH_CLIENT_SECRET"]
DISCORD_CHANNEL_ID = int(tokens["DISCORD_CHANNEL_ID"])
TWITCH_USERNAMES = load_twitch_usernames() # Load the usernames at startup
CHECK_INTERVAL = 60  # Time in seconds between checks

# Define the /addtwitch command
@bot.tree.command(name="addtwitch", description="Add a Twitch username to the list (Moderator only).")
@app_commands.describe(username="The Twitch username to add.")
async def addtwitch(interaction: discord.Interaction, username: str):
    # Check if the user has the "Mod" role
    if discord.utils.get(interaction.user.roles, name="Mod"):
        username = username.strip()
        if username not in TWITCH_USERNAMES:
            TWITCH_USERNAMES.append(username)
            save_twitch_usernames(TWITCH_USERNAMES)  # Save the updated list to the file
            await interaction.response.send_message(f"Added {username} to the Twitch usernames list.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{username} is already in the Twitch usernames list.", ephemeral=True)
    else:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

# Define the /rmtwitch command
print("Registering /rmtwitch command")
@bot.tree.command(name="rmtwitch", description="Remove a Twitch username from the list (Moderator only).")
@app_commands.describe(username="The Twitch username to remove.")
async def rmtwitch(interaction: discord.Interaction, username: str):
    # Check if the user has the "Mod" role
    if discord.utils.get(interaction.user.roles, name="Mod"):
        username = username.strip()
        if username in TWITCH_USERNAMES:
            TWITCH_USERNAMES.remove(username)
            save_twitch_usernames(TWITCH_USERNAMES)  # Save the updated list to the file            
            await interaction.response.send_message(f"Removed {username} from the Twitch usernames list.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{username} is not in the Twitch usernames list.", ephemeral=True)
    else:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

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
                if len(data["data"]) > 0:  # If data is not empty, the user is live
                    live_users.append(username)
    return live_users

async def notify_when_live():
    """Periodically check if Twitch users are live and send notifications."""
    access_token = await get_twitch_access_token()
    notified_users = set()  # Keep track of users already notified
    while True:
        try:
            live_users = await check_live_status(access_token, TWITCH_USERNAMES)
            channel = bot.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                for user in live_users:
                    if user not in notified_users:
                        if user == "EGV2008":
                            await channel.send(f"I'm now live on Twitch!! Come say hi!! https://www.twitch.tv/{user} @everyone")
                        else:
                            await channel.send(f"{user} is now live on Twitch!! Go check them out!! https://www.twitch.tv/{user} @everyone")
                        notified_users.add(user)
                # Remove users who are no longer live from the notified list
                notified_users = notified_users.intersection(live_users)
        except Exception as e:
            print(f"Error checking Twitch live status: {e}")
        await asyncio.sleep(CHECK_INTERVAL)


# Event to sync the slash commands with Discord
@bot.event
async def on_ready():
    bot.loop.create_task(notify_when_live())  # Start the live notification task
    await bot.tree.sync()  # Sync the slash commands with Discord
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
