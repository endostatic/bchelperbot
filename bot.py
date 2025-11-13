#---------------------------------
# BitCraft Helper Bot Entry Point
#---------------------------------

import discord
import io
from discord.ext import commands
from discord import app_commands
import importlib
import requests, asyncio, os
from io import BytesIO

# -------------------------------------------------
# Local imports
# -------------------------------------------------
import constants, dev, helpers, skillpillow, commands as bot_commands

# -------------------------------------------------
# Token
# -------------------------------------------------
TOKEN = constants.BOT_TOKEN

# -------------------------------------------------
# Intents and Bot Setup
# -------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# -------------------------------------------------
# Reload dev module for development commands
# -------------------------------------------------
importlib.reload(dev)

# -------------------------------------------------
# Register commands from the modular command system
# -------------------------------------------------
bot_commands.setup(bot)

# -------------------------------------------------
# Caches
# -------------------------------------------------
last_char = {}
last_emp = {}
last_clm = {}
user_empire_monitor = {}  # {user_id: {"task": ..., "eid": ..., "name": ..., "alerts": {}, "channel_id": ...}}

# -------------------------------------------------
# Ready event
# -------------------------------------------------
@bot.event
async def on_ready():
    print("✅ BitCraft Helper Bot is now online.")
    try:
        synced = await bot.tree.sync()
        print(f"✅ BitCraft Helper Bot is ready with {len(synced)} slash commands!")
    except Exception as e:
        print(f"❌ Failed to sync slash commands: {e}")

    # Optional channel notification
    channel = discord.utils.get(bot.get_all_channels(), name=constants.STARTUP_CHANNEL_NAME)
    if channel:
        try:
            await helpers.send_pillow_text(channel, "BitCraft Helper Bot is online! ✅", width=450, height=80)
            print(f"Message sent in #{channel.name}")
        except Exception as e:
            print(f"❌ Could not send message: {e}")
    else:
        print(f"❌ No channel named '{constants.STARTUP_CHANNEL_NAME}' found.")

# -------------------------------------------------
# Developer command
# -------------------------------------------------
@bot.command(name="reload_helpers")
async def reload_helpers(ctx):
    importlib.reload(dev)
    await ctx.send("✅ Dev module reloaded!")  # Developer output exception remains direct

# -------------------------------------------------
# Run the bot
# -------------------------------------------------
bot.run(TOKEN)
