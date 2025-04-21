import discord
from discord import app_commands
from utils import save_twitch_usernames, tokens, TWITCH_USERNAMES, STREAMER

SOCIALS_CHANNEL_ID = int(tokens["SOCIALS_CHANNEL_ID"])

# /addtwitch
@app_commands.command(name="addtwitch", description="Add a Twitch username to the list (Moderator only).")
@app_commands.describe(username="The Twitch username to add.")
async def addtwitch(interaction: discord.Interaction, username: str):
    if discord.utils.get(interaction.user.roles, name="Mod, Streamer"):
        username = username.strip()
        if username not in TWITCH_USERNAMES:
            TWITCH_USERNAMES.append(username)
            save_twitch_usernames(TWITCH_USERNAMES)
            await interaction.response.send_message(
                f"Added {username} to the Twitch usernames list.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"{username} is already in the Twitch usernames list.", ephemeral=True
            )
    else:
        await interaction.response.send_message(
            "You do not have permission to use this command.", ephemeral=True
        )

# /rmtwitch
@app_commands.command(name="rmtwitch", description="Remove a Twitch username from the list (Moderator only).")
@app_commands.describe(username="The Twitch username to remove.")
async def rmtwitch(interaction: discord.Interaction, username: str):
    if discord.utils.get(interaction.user.roles, name="Mod, Streamer"):
        username = username.strip()
        if username in TWITCH_USERNAMES:
            TWITCH_USERNAMES.remove(username)
            save_twitch_usernames(TWITCH_USERNAMES)
            await interaction.response.send_message(
                f"Removed {username} from the Twitch usernames list.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"{username} is not in the Twitch usernames list.", ephemeral=True
            )
    else:
        await interaction.response.send_message(
            "You do not have permission to use this command.", ephemeral=True
        )

# /socials
@app_commands.command(name="socials", description="Send to links channel.")
async def socials(interaction: discord.Interaction):
    socials_channel = interaction.guild.get_channel(SOCIALS_CHANNEL_ID)
    if socials_channel:
        await interaction.response.send_message(
            f"{STREAMER}'s socials and links can be found in {socials_channel.mention}.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "The #links channel could not be found. Please contact an admin.", ephemeral=True
        )

# List of commands to register with the bot
commands_list = [addtwitch, rmtwitch, socials]