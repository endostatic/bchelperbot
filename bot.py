#---------------------------------
# BitCraft Helper Bot Entry Point
#---------------------------------
# bot.py
import discord
from discord.ext import commands
from constants import CONSTANTS
from commands import register_commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=CONSTANTS["BOT_PREFIX"], intents=intents)

# -------------------------------
# Event: on_ready
# -------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await register_commands(bot)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

def register_commands(bot: commands.Bot)
    commands_list = [
        "commands",
        "setchar",
        "skill",
        "skillgrid",
        "equipment",
        "setempire",
        "watchtowers"
    ]
for cmd_name in commands_list:

        # -------------------------------
        # Prefix registration
        # -------------------------------
        @bot.command(name=cmd_name)
        async def generic_prefix_command(ctx: commands.Context, *, arg: str = None, cmd_name=cmd_name) -> None:
            if cmd_name == "skill":
                if not validate_input(arg):
                    await ctx.send("Invalid skill name.")
                    return
                image = await asyncio.to_thread(generate_skill_image_async, arg)
                await ctx.send(file=image)

            elif cmd_name == "setchar":
                if not validate_input(arg):
                    await ctx.send("Invalid character name.")
                    return
                embed = await asyncio.to_thread(send_generic_image_async, "setchar", arg)
                await ctx.send(embed=embed)

            else:
                # Placeholder/future implementation
                await ctx.send(f"Command '{cmd_name}' executed. (Handler not yet implemented)")

        # -------------------------------
        # Slash registration
        # -------------------------------
        @bot.tree.command(name=cmd_name)
        async def generic_slash_command(interaction: Interaction, arg: str = None, cmd_name=cmd_name) -> None:
            if cmd_name == "skill":
                if not validate_input(arg):
                    await interaction.response.send_message("Invalid skill name.")
                    return
                image = await asyncio.to_thread(generate_skill_image_async, arg)
                await interaction.response.send_message(file=image)

            elif cmd_name == "setchar":
                if not validate_input(arg):
                    await interaction.response.send_message("Invalid character name.")
                    return
                embed = await asyncio.to_thread(send_generic_image_async, "setchar", arg)
                await interaction.response.send_message(embed=embed)

            else:
                await interaction.response.send_message(f"Command '{cmd_name}' executed. (Handler not yet implemented)")
                
# -------------------------------
# Bot entry point
# -------------------------------
if __name__ == "__main__":
    bot.run(CONSTANTS["BOT_TOKEN"])


