import json
import os
import aiohttp

STREAMER = "EGV2008"
TWITCH_USERNAMES_FILE = os.getenv("TWITCH_USERNAMES_FILE", "twitch_usernames.json")

def get_env_variable(name):
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing environment variable: {name}")
    return value

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

# Hent inn Twtich Access Token
async def get_twitch_access_token():
    url = "https://id.twitch.tv/oauth2/token"

    params = {
        "client_id": get_env_variable("TWITCH_CLIENT_ID"),
        "client_secret": get_env_variable("TWITCH_CLIENT_SECRET"),
        "grant_type": "client_credentials"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params) as response:
            if response.status != 200:
                raise Exception(f"Twitch API error: {response.status}")

            data = await response.json()

            if "access_token" not in data:
                raise Exception("No access token in response")

            return data["access_token"]
