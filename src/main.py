import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load .env first, the imports below read env vars
load_dotenv()

import db
from commands import commands_list
from twitch_notif import notify_when_live
from utils import get_env_variable

DISCORD_TOKEN = get_env_variable("DISCORD_TOKEN")


class Bot(commands.Bot):
    def __init__(self):
        # Slash commands only, so no privileged intents. Mentions are off unless a message allows them
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=discord.Intents.default(),
            allowed_mentions=discord.AllowedMentions.none()
        )
        self.db = None

    # Runs once at startup, before connecting to Discord
    async def setup_hook(self):
        self.db = await db.connect()
        print(f"Database ready at {db.DATABASE_PATH}")

        for command in commands_list:
            self.tree.add_command(command)
        await self.tree.sync()

        print("Starting Twitch notifier...")
        notify_when_live.start(self)

    async def on_ready(self):
        print(f"Logged in as {self.user} in {len(self.guilds)} server(s)")

    # Bot was removed from a server, drop its config and watch list
    async def on_guild_remove(self, guild):
        await db.delete_guild(self.db, guild.id)
        print(f"Removed config for guild {guild.id}")

    async def close(self):
        notify_when_live.cancel()
        if self.db is not None:
            await self.db.close()
        await super().close()


if __name__ == "__main__":
    print("Starting bot...")
    try:
        Bot().run(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        print("Invalid DISCORD_TOKEN")
        raise
    # Other crashes exit, Docker restarts the bot
