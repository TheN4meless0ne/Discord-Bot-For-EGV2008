import re
from typing import Optional

import discord
from discord import app_commands

import db
from changelog import BOT_VERSION

# Twitch logins: letters, numbers and underscores
LOGIN_RE = re.compile(r"[a-z0-9][a-z0-9_]{2,24}")
MAX_WATCHED = 100
MAX_AVATAR_BYTES = 8 * 1024 * 1024

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

# The management commands need Manage Server by default.
# Admins can change who may use them under Server Settings > Integrations.

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

# List of commands to register with the bot
commands_list = [setup, botprofile, twitch, changelog, socials]
