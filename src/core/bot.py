import asyncio

import discord
from discord.ext import commands

from core import db
from changelog.announce import announce_changes
from changelog.commands import COMMANDS as CHANGELOG_COMMANDS
from server.commands import COMMANDS as SERVER_COMMANDS
from twitch.commands import COMMANDS as TWITCH_COMMANDS
from twitch.notifier import notify_when_live


class Bot(commands.Bot):
    def __init__(self):
        # Slash commands only, so no privileged intents. Mentions are off unless a message allows them
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=discord.Intents.default(),
            allowed_mentions=discord.AllowedMentions.none()
        )
        self.db = None
        self.changelog_task = None

    # Runs once at startup, before connecting to Discord
    async def setup_hook(self):
        self.db = await db.connect()
        print(f"Database ready at {db.DATABASE_PATH}")

        for command in SERVER_COMMANDS + TWITCH_COMMANDS + CHANGELOG_COMMANDS:
            self.tree.add_command(command)
        await self.tree.sync()

        print("Starting Twitch notifier...")
        notify_when_live.start(self)

        # Once per start, after an update has been deployed
        self.changelog_task = asyncio.create_task(announce_changes(self))

    async def on_ready(self):
        print(f"Logged in as {self.user} in {len(self.guilds)} server(s)")

    # Bot was removed from a server, drop its config and watch list
    async def on_guild_remove(self, guild):
        await db.delete_guild(self.db, guild.id)
        print(f"Removed config for guild {guild.id}")

    async def close(self):
        notify_when_live.cancel()
        if self.changelog_task is not None:
            self.changelog_task.cancel()
        if self.db is not None:
            await self.db.close()
        await super().close()
