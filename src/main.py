from dotenv import load_dotenv

# Load .env first, the imports below read env vars
load_dotenv()

import discord

from core.bot import Bot
from core.utils import get_env_variable

DISCORD_TOKEN = get_env_variable("DISCORD_TOKEN")

if __name__ == "__main__":
    print("Starting bot...")
    try:
        Bot().run(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        print("Invalid DISCORD_TOKEN")
        raise
    # Other crashes exit, Docker restarts the bot
