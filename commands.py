#-----------------------------------
# Commands
#-----------------------------------
import discord
from discord.ext import commands
from skillpillow import _skill_command
import helpers, constants

def setup_commands(bot):

    # -------------------------------------------------
    # /commands or !commands
    # -------------------------------------------------
    @bot.hybrid_command(name="commands", with_app_command=True, description="List available commands.")
    async def commands_list(ctx: commands.Context):
        await helpers.send_commands_dashboard(ctx)

    # -------------------------------------------------
    # /setchar or !setchar
    # -------------------------------------------------
    @bot.hybrid_command(name="setchar", with_app_command=True, description="Set your active character.")
    async def setchar(ctx: commands.Context, *, character_name: str):
        user_id = str(ctx.author.id)
        helpers.set_user_character(user_id, character_name)
        await helpers.send_setchar_confirmation(ctx, character_name)

    # -------------------------------------------------
    # /skill or !skill
    # -------------------------------------------------
    @bot.hybrid_command(name="skill", with_app_command=True, description="Show skill XP and time estimates.")
    async def skill(ctx: commands.Context, *, skill_name: str = None):
        user_id = ctx.author.id
        await _skill_command(ctx, user_id)

def setup(bot):
    setup_commands(bot)
