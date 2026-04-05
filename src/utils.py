import json
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

STREAMER = "EGV2008"
TWITCH_USERNAMES_FILE = os.getenv("TWITCH_USERNAMES_FILE", "twitch_usernames.json")

# Hent Twitch-brukernavn fra en fil
# Hvis filen ikke finnes, returner en liste med standard brukernavn
def load_twitch_usernames():
    try:
        with open(TWITCH_USERNAMES_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return [STREAMER]

# Save Twitch usernames to a file
def save_twitch_usernames(usernames):
    usernames_dir = os.path.dirname(TWITCH_USERNAMES_FILE)
    if usernames_dir:
        os.makedirs(usernames_dir, exist_ok=True)
    with open(TWITCH_USERNAMES_FILE, "w") as file:
        json.dump(usernames, file)

def load_tokens():
    """Load required config values from environment variables (.env)."""
    required_keys = [
        "DISCORD_TOKEN",
        "TWITCH_CLIENT_SECRET",
        "TWITCH_CLIENT_ID",
        "SOCIALS_CHANNEL_ID",
        "NOTIF_CHANNEL_ID",
        "GUILD_ID",
    ]
    tokens = {}
    missing = []

    for key in required_keys:
        value = os.getenv(key)
        if value is None or value == "":
            missing.append(key)
        else:
            tokens[key] = value

    if missing:
        missing_str = ", ".join(missing)
        raise ValueError(
            "Missing required environment variables: "
            f"{missing_str}. If you are running Docker directly, use --env-file .env "
            "or pass each variable with -e."
        )

    return tokens

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

# variables and constants
tokens = load_tokens()
TWITCH_USERNAMES = load_twitch_usernames()

TWITCH_CLIENT_SECRET = tokens["TWITCH_CLIENT_SECRET"]
TWITCH_CLIENT_ID = tokens["TWITCH_CLIENT_ID"]