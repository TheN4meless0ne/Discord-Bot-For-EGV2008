import os
import asyncio
import discord
from discord.ext import commands
from commands import commands_list
from twitch_notif import notify_when_live
from utils import get_env_variable
from dotenv import load_dotenv

# Load .env locally (ignored in Azure)
load_dotenv()

DISCORD_TOKEN = get_env_variable("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)


# Registrer kommands from commands.py and adds to Discord bot
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    for command in commands_list:
        bot.tree.add_command(command)

    print("Starting Twitch notifier...")
    asyncio.create_task(notify_when_live(bot))

    await bot.tree.sync()

# Run Discord bot
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)


if __name__ == '__main__':
    print("Starting bot...")

    while True:
        try:
            bot.run(DISCORD_TOKEN)

        except discord.errors.PrivilegedIntentsRequired:
            print(
                'Missing "Message Content Intent". Enable it at:\n'
                'https://discord.com/developers/applications'
            )

        except discord.errors.LoginFailure:
            print("Invalid DISCORD_TOKEN")

        except Exception as e:
            print(f"Bot crashed: {e}")
