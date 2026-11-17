from typing import Optional

import discord
from discord import app_commands

MAX_AVATAR_BYTES = 8 * 1024 * 1024

# /setup
@app_commands.command(name="setup", description="Show or change this server's bot settings.")
@app_commands.describe(
    notif_channel="Channel for Twitch live notifications.",
    socials_channel="Channel that /socials points to.",
    alert_role="Role to mention when someone goes live.",
    streamer="Twitch username of this server's own streamer."
)
@app_commands.guild_only()
@app_commands.default_permissions(manage_guild=True)
async def setup(
    interaction: discord.Interaction,
    notif_channel: Optional[discord.TextChannel] = None,
    socials_channel: Optional[discord.TextChannel] = None,
    alert_role: Optional[discord.Role] = None,
    streamer: Optional[str] = None
):
    conn = interaction.client.db
    fields = {}
    warnings = []

    if notif_channel:
        fields["notif_channel_id"] = notif_channel.id
        permissions = notif_channel.permissions_for(interaction.guild.me)
        if not (permissions.view_channel and permissions.send_messages):
            warnings.append(f"I can't send messages in {notif_channel.mention} yet.")

    if socials_channel:
        fields["socials_channel_id"] = socials_channel.id

    if alert_role:
        fields["alert_role_id"] = alert_role.id
        if not alert_role.mentionable and not interaction.guild.me.guild_permissions.mention_everyone:
            warnings.append(
                f'I need the "Mention @everyone, @here and All Roles" permission to ping {alert_role.name}.'
            )

    if streamer:
        streamer = db.normalise(streamer)
        if not LOGIN_RE.fullmatch(streamer):
            await interaction.response.send_message(
                "That is not a valid Twitch username.", ephemeral=True
            )
            return
        fields["streamer_login"] = streamer

    if fields:
        await db.upsert_guild_config(conn, interaction.guild_id, **fields)

    # The server's own streamer is always watched
    if streamer:
        await db.add_watched(conn, interaction.guild_id, streamer)

    config = await db.get_guild_config(conn, interaction.guild_id)

    # The @everyone role has the server's ID and can't be mentioned by ID
    alert_role_id = config and config["alert_role_id"]
    if not alert_role_id:
        alert_role_text = "not set"
    elif alert_role_id == interaction.guild_id:
        alert_role_text = "@everyone"
    else:
        alert_role_text = f"<@&{alert_role_id}>"

    def show(value, template):
        return template.format(value) if value else "not set"

    lines = [
        "Settings saved." if fields else "Current settings:",
        "Notification channel: " + show(config and config["notif_channel_id"], "<#{}>"),
        "Socials channel: " + show(config and config["socials_channel_id"], "<#{}>"),
        "Alert role: " + alert_role_text,
        "Streamer: " + show(config and config["streamer_login"], "{}"),
        "Changelog: " + (
            f"on in <#{config['changelog_channel_id']}>"
            if config and config["changelog_enabled"] and config["changelog_channel_id"]
            else "off"
        ),
    ]

    await interaction.response.send_message("\n".join(lines + warnings), ephemeral=True)

# /botprofile
@app_commands.command(name="botprofile", description="Change the bot's name and avatar in this server.")
@app_commands.describe(
    nickname="Name to show in this server.",
    avatar="Image to use as avatar in this server.",
    reset="Go back to the bot's default name and avatar."
)
@app_commands.guild_only()
@app_commands.default_permissions(manage_guild=True)
async def botprofile(
    interaction: discord.Interaction,
    nickname: Optional[app_commands.Range[str, 1, 32]] = None,
    avatar: Optional[discord.Attachment] = None,
    reset: bool = False
):
    changes = {}

    if reset:
        changes = {"nick": None, "avatar": None}
    if nickname:
        changes["nick"] = nickname
    if avatar:
        if not (avatar.content_type or "").startswith("image/") or avatar.size > MAX_AVATAR_BYTES:
            await interaction.response.send_message(
                "The avatar must be an image under 8 MB.", ephemeral=True
            )
            return
        changes["avatar"] = await avatar.read()

    if not changes:
        await interaction.response.send_message(
            "Give a nickname, an avatar, or set reset.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    try:
        await interaction.guild.me.edit(**changes)
    except discord.Forbidden:
        await interaction.followup.send(
            'I need the "Change Nickname" permission to do that.', ephemeral=True
        )
        return
    except discord.HTTPException as e:
        await interaction.followup.send(f"Discord rejected the change: {e.text}", ephemeral=True)
        return

    await interaction.followup.send("Updated my profile for this server.", ephemeral=True)

# /socials
@app_commands.command(name="socials", description="Send to links channel.")
@app_commands.guild_only()
async def socials(interaction: discord.Interaction):
    config = await db.get_guild_config(interaction.client.db, interaction.guild_id)
    channel_id = config and config["socials_channel_id"]
    socials_channel = interaction.guild.get_channel(channel_id) if channel_id else None

    if socials_channel:
        owner = f"{config['streamer_login']}'s socials" if config["streamer_login"] else "The socials"

        await interaction.response.send_message(
            f"{owner} can be found in {socials_channel.mention}.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "The socials channel has not been set up. Please contact an admin.",
            ephemeral=True
        )

COMMANDS = [setup, botprofile, socials]
