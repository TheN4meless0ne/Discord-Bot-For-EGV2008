import discord
from discord import app_commands

from core import db
from changelog.announce import BOT_VERSION

# /changelog on, /changelog off
changelog = app_commands.Group(
    name="changelog",
    description="Post a message here when the bot is updated.",
    guild_only=True,
    allowed_contexts=app_commands.AppCommandContext(guild=True),
    default_permissions=discord.Permissions(manage_guild=True)
)

# /changelog on
@changelog.command(name="on", description="Post update messages in a channel.")
@app_commands.describe(channel="Channel for update messages.")
async def changelog_on(interaction: discord.Interaction, channel: discord.TextChannel):
    permissions = channel.permissions_for(interaction.guild.me)
    if not (permissions.view_channel and permissions.send_messages):
        await interaction.response.send_message(
            f"I can't send messages in {channel.mention}.", ephemeral=True
        )
        return

    # Start from the running version, so earlier updates are not posted
    await db.upsert_guild_config(
        interaction.client.db, interaction.guild_id,
        changelog_enabled=1, changelog_channel_id=channel.id, changelog_sha=BOT_VERSION or None
    )

    await interaction.response.send_message(
        f"Update messages will be posted in {channel.mention}.", ephemeral=True
    )

# /changelog off
@changelog.command(name="off", description="Stop posting update messages.")
async def changelog_off(interaction: discord.Interaction):
    await db.upsert_guild_config(interaction.client.db, interaction.guild_id, changelog_enabled=0)

    await interaction.response.send_message("Update messages are turned off.", ephemeral=True)

COMMANDS = [changelog]
