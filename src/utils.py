import json
import aiohttp

# Hent Twitch-brukernavn fra en fil
# Hvis filen ikke finnes, returner en liste med standard brukernavn
def load_twitch_usernames():
    try:
        with open("twitch_usernames.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return [STREAMER]

# Save Twitch usernames to a file
def save_twitch_usernames(usernames):
    with open("twitch_usernames.json", "w") as file:
        json.dump(usernames, file)

# Load tokens from token.txt
def load_tokens():
    tokens = {}
    with open("token.txt", "r") as file:
        for line in file:
            key, value = line.strip().split("=")
            tokens[key] = value
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

STREAMER = "EGV2008"