import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load .env first, the imports below read env vars
load_dotenv()

import db
from commands import commands_list
from twitch_notif import notify_when_live
from utils import get_env_variable, STREAMER, TWITCH_USERNAMES_FILE, DEFAULT_TWITCH_USERNAMES_FILE

DISCORD_TOKEN = get_env_variable("DISCORD_TOKEN")

# Old single-server settings, imported into the database once
LEGACY_GUILD_ID = os.getenv("GUILD_ID")
LEGACY_ALERT_ROLE_NAME = "Wants Alerts"


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="/", intents=intents)
        self.db = None

    # Runs once at startup, before connecting to Discord
    async def setup_hook(self):
        self.db = await db.connect()
        print(f"Database ready at {db.DATABASE_PATH}")

        if LEGACY_GUILD_ID:
            imported = await db.import_legacy_config(
                self.db,
                guild_id=int(LEGACY_GUILD_ID),
                notif_channel_id=_int_or_none(os.getenv("NOTIF_CHANNEL_ID")),
                socials_channel_id=_int_or_none(os.getenv("SOCIALS_CHANNEL_ID")),
                streamer_login=STREAMER,
                usernames_files=[TWITCH_USERNAMES_FILE, DEFAULT_TWITCH_USERNAMES_FILE],
            )
            if imported:
                print(f"Imported legacy config for guild {LEGACY_GUILD_ID}")

        for command in commands_list:
            self.tree.add_command(command)
        await self.tree.sync()

        print("Starting Twitch notifier...")
        asyncio.create_task(notify_when_live(self))

    async def on_ready(self):
        print(f"Logged in as {self.user} in {len(self.guilds)} server(s)")

        if LEGACY_GUILD_ID:
            await self.link_legacy_alert_role()

    # Find the old alert role by name and store its ID. Retried until found
    async def link_legacy_alert_role(self):
        guild_id = int(LEGACY_GUILD_ID)
        config = await db.get_guild_config(self.db, guild_id)
        if config is None or config["alert_role_id"] is not None:
            return

        guild = self.get_guild(guild_id)
        role = guild and discord.utils.get(guild.roles, name=LEGACY_ALERT_ROLE_NAME)
        if role:
            await db.upsert_guild_config(self.db, guild_id, alert_role_id=role.id)
            print(f"Linked alert role '{role.name}' ({role.id})")

    # Bot was removed from a server, drop its config and watch list
    async def on_guild_remove(self, guild):
        await db.delete_guild(self.db, guild.id)
        print(f"Removed config for guild {guild.id}")

    async def close(self):
        if self.db is not None:
            await self.db.close()
        await super().close()


def _int_or_none(value):
    return int(value) if value else None


if __name__ == "__main__":
    print("Starting bot...")
    try:
        Bot().run(DISCORD_TOKEN)
    except discord.errors.PrivilegedIntentsRequired:
        print(
            'Missing "Message Content Intent". Enable it at:\n'
            "https://discord.com/developers/applications"
        )
        raise
    except discord.errors.LoginFailure:
        print("Invalid DISCORD_TOKEN")
        raise
    # Other crashes exit, Docker restarts the bot
