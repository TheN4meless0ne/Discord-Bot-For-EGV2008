import os
import re

import aiohttp
import discord

import db

# Set at build time by the GitHub workflow, empty when running from source
BOT_VERSION = os.getenv("BOT_VERSION", "")
BOT_REPO = os.getenv("BOT_REPO", "")

TIMEOUT = aiohttp.ClientTimeout(total=30)
MERGE_RE = re.compile(r"Merge pull request (#\d+)")


# One line per change on main: merged PR titles and direct pushes
async def get_changes(base, head):
    url = f"https://api.github.com/repos/{BOT_REPO}/compare/{base}...{head}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "discord-bot"}

    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise RuntimeError(f"GitHub compare error: {response.status}")
            body = await response.json()

    commits = {commit["sha"]: commit for commit in body["commits"]}
    lines = []

    # Follow main's own history, skipping commits that came in through a PR
    sha = body["commits"][-1]["sha"] if body["commits"] else None
    while sha in commits:
        commit = commits[sha]
        message = commit["commit"]["message"].strip().splitlines()
        merge = MERGE_RE.match(message[0])

        if merge:
            # GitHub puts the PR title after a blank line
            title = message[2] if len(message) > 2 else message[0]
            lines.append(f"- {title} ({merge.group(1)})")
        else:
            lines.append(f"- {message[0]}")

        sha = commit["parents"][0]["sha"] if commit["parents"] else None

    lines.reverse()
    return lines


def build_messages(lines, base, head, limit=1900):
    link = f"<https://github.com/{BOT_REPO}/compare/{base[:7]}...{head[:7]}>"
    header = f"**Bot updated** (`{head[:7]}`)\n"

    messages = []
    text = header
    for line in [line[:200] for line in lines] + [link]:
        if len(text) + len(line) + 1 > limit:
            messages.append(text)
            text = ""
        text += line + "\n"
    messages.append(text)
    return messages


# Post what changed on main since each server last heard
async def announce_changes(bot):
    if not BOT_VERSION or not BOT_REPO:
        print("Changelog skipped: no BOT_VERSION, running from source")
        return

    await bot.wait_until_ready()
    changes = {}

    for config in await db.changelog_guilds(bot.db):
        base = config["changelog_sha"]

        # Not set yet, start from this version
        if not base:
            await db.upsert_guild_config(bot.db, config["guild_id"], changelog_sha=BOT_VERSION)
            continue
        if base == BOT_VERSION:
            continue

        guild = bot.get_guild(config["guild_id"])
        channel = guild and guild.get_channel(config["changelog_channel_id"])
        if channel is None:
            continue

        try:
            if base not in changes:
                changes[base] = await get_changes(base, BOT_VERSION)

            # Nothing to list, e.g. after a revert
            if changes[base]:
                for message in build_messages(changes[base], base, BOT_VERSION):
                    await channel.send(message)
        except (RuntimeError, aiohttp.ClientError, discord.HTTPException) as e:
            # Kept as is, so the next start tries again
            print(f"Changelog failed for guild {config['guild_id']}: {e}")
            continue

        await db.upsert_guild_config(bot.db, config["guild_id"], changelog_sha=BOT_VERSION)
