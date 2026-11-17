import re

import discord
from discord import app_commands

from core import db

# Twitch logins: letters, numbers and underscores
LOGIN_RE = re.compile(r"[a-z0-9][a-z0-9_]{2,24}")
MAX_WATCHED = 100

def chunk_list(items, limit=1900):
    chunk = ""
    for item in items:
        if len(chunk) + len(item) + 1 > limit:
            yield chunk
            chunk = item + "\n"
        else:
            chunk += item + "\n"
    if chunk:
        yield chunk

# /twitch add, /twitch remove, /twitch list
twitch = app_commands.Group(
    name="twitch",
    description="Manage the Twitch usernames monitored in this server.",
    guild_only=True,
    allowed_contexts=app_commands.AppCommandContext(guild=True),
    default_permissions=discord.Permissions(manage_guild=True)
)

# /twitch add
@twitch.command(name="add", description="Add a Twitch username to this server's list.")
@app_commands.describe(username="The Twitch username to add.")
async def twitch_add(interaction: discord.Interaction, username: str):
    conn = interaction.client.db
    username = db.normalise(username)

    if not LOGIN_RE.fullmatch(username):
        await interaction.response.send_message(
            "That is not a valid Twitch username.", ephemeral=True
        )
        return

    if await db.count_watched(conn, interaction.guild_id) >= MAX_WATCHED:
        await interaction.response.send_message(
            f"This server already has {MAX_WATCHED} Twitch usernames, remove one first.",
            ephemeral=True
        )
        return

    if await db.add_watched(conn, interaction.guild_id, username):
        print(f"Added Twitch user {username} in guild {interaction.guild_id}")

        await interaction.response.send_message(
            f"Added {username} to the Twitch usernames list.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"{username} is already in the Twitch usernames list.", ephemeral=True
        )

# /twitch remove
@twitch.command(name="remove", description="Remove a Twitch username from this server's list.")
@app_commands.describe(username="The Twitch username to remove.")
async def twitch_remove(interaction: discord.Interaction, username: str):
    username = db.normalise(username)

    if await db.remove_watched(interaction.client.db, interaction.guild_id, username):
        print(f"Removed Twitch user {username} in guild {interaction.guild_id}")

        await interaction.response.send_message(
            f"Removed {username} from the Twitch usernames list.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "That username is not in the Twitch usernames list.", ephemeral=True
        )

# Suggest usernames from this server's list while typing
@twitch_remove.autocomplete("username")
async def twitch_remove_autocomplete(interaction: discord.Interaction, current: str):
    usernames = await db.list_watched(interaction.client.db, interaction.guild_id)
    current = current.strip().lower()

    # Discord shows at most 25 suggestions
    return [
        app_commands.Choice(name=name, value=name)
        for name in usernames if current in name
    ][:25]

# /twitch list
@twitch.command(name="list", description="List the Twitch usernames monitored in this server.")
async def twitch_list(interaction: discord.Interaction):
    usernames = await db.list_watched(interaction.client.db, interaction.guild_id)

    if usernames:
        message = "Currently monitored Twitch usernames:\n"

        for i, chunk in enumerate(chunk_list(usernames)):
            if i == 0:
                await interaction.response.send_message(
                    message + chunk,
                    ephemeral=True
                )
            else:
                await interaction.followup.send(chunk, ephemeral=True)

    else:
        await interaction.response.send_message(
            "No Twitch usernames are currently being monitored.",
            ephemeral=True
        )

COMMANDS = [twitch]
