import discord
from discord import app_commands

from utils import (
    save_twitch_usernames,
    load_twitch_usernames,
    get_env_variable,
    STREAMER
)

SOCIALS_CHANNEL_ID = int(get_env_variable("SOCIALS_CHANNEL_ID"))

def has_permission(member):
    if not hasattr(member, "roles"):
        return False

    return (
        discord.utils.get(member.roles, name="Mod") or
        discord.utils.get(member.roles, name="Streamer")
    )

# /addtwitch (Moderator only)
# /addtwitch
@app_commands.command(name="addtwitch", description="Add a Twitch username (Moderator only).")
@app_commands.describe(username="The Twitch username to add.")
async def addtwitch(interaction: discord.Interaction, username: str):
    if not has_permission(interaction.user):
        await interaction.response.send_message(
            "You do not have permission to use this command.", ephemeral=True
        )
        return

    usernames = load_twitch_usernames()
    username = username.strip()

    if username not in usernames:
        usernames.append(username)
        save_twitch_usernames(usernames)

        print(f"Added Twitch user: {username}")

        await interaction.response.send_message(
            f"Added {username} to the Twitch usernames list.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"{username} is already in the Twitch usernames list.", ephemeral=True
        )

# /rmtwitch (Moderator only)
@app_commands.command(name="rmtwitch", description="Remove a Twitch username (Moderator only).")
@app_commands.describe(username="The Twitch username to remove.")
async def rmtwitch(interaction: discord.Interaction, username: str):
    if not has_permission(interaction.user):
        await interaction.response.send_message(
            "You do not have permission to use this command.", ephemeral=True
        )
        return

    usernames = load_twitch_usernames()
    username = username.strip()

    if username in usernames:
        usernames.remove(username)
        save_twitch_usernames(usernames)

        print(f"Removed Twitch user: {username}")

        await interaction.response.send_message(
            f"Removed {username} from the Twitch usernames list.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"{username} is not in the Twitch usernames list.", ephemeral=True
        )

# /listtwitch (Moderator only)
@app_commands.command(name="listtwitch", description="List all Twitch usernames being monitored (Moderator only).")
async def listtwitch(interaction: discord.Interaction):
    if not has_permission(interaction.user):
        await interaction.response.send_message(
            "You do not have permission to use this command.", ephemeral=True
        )
        return
  
    if TWITCH_USERNAMES:
        usernames_list = "\n".join(TWITCH_USERNAMES)
        await interaction.response.send_message(
            f"Currently monitored Twitch usernames:\n{usernames_list}", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "No Twitch usernames are currently being monitored.", ephemeral=True
        )

# /socials
@app_commands.command(name="socials", description="Send to links channel.")
async def socials(interaction: discord.Interaction):
    socials_channel = interaction.guild.get_channel(SOCIALS_CHANNEL_ID)

    if socials_channel:
        await interaction.response.send_message(
            f"{STREAMER}'s socials can be found in {socials_channel.mention}.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "The #links channel could not be found. Please contact an admin.",
            ephemeral=True
        )

# List of commands to register with the bot
commands_list = [addtwitch, rmtwitch, listtwitch, socials]
