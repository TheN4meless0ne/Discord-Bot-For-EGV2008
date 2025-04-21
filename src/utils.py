import json

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

# Shared variables
TWITCH_USERNAMES = load_twitch_usernames()
tokens = load_tokens()
STREAMER = "EGV2008"