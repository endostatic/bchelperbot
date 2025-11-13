#---------------------------------
# Pillow outputs for Skill Command
#---------------------------------
import os
import io
import asyncio
from PIL import Image, ImageDraw, ImageFont
import discord
from discord.ext import commands
import constants, helpers
from helpers import dhm, get_skill_stats, player, inv, last_char, RAR, SKILL

# -------------------------------------------------
# Full skill dashboard image
# -------------------------------------------------
async def send_skills_dashboard(ctx_or_interaction, player_data, inventory):
    SKILL_ORDER = constants.SKILL_ORDER

    width, row_height, padding = 450, 50, 20
    height = padding * 2 + row_height * len(SKILL_ORDER)
    img = Image.new("RGBA", (width, height), (30, 30, 35, 255))
    draw = ImageDraw.Draw(img)

    font_title = ImageFont.truetype(constants.FONT_BOLD_PATH, 24)
    font_row   = ImageFont.truetype(constants.FONT_REGULAR_PATH, 20)

    # Title
    title = "Select a Skill"
    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_height = title_bbox[3] - title_bbox[1]
    draw.text(((width - (title_bbox[2] - title_bbox[0])) // 2, 10), title, font=font_title, fill=constants.FONT_COLOR)

    # Grid lines
    start_y = 10 + title_height + 10
    for i in range(len(SKILL_ORDER)+1):
        y = start_y + i * row_height
        draw.line([(10, y), (width-10, y)], fill=(100,100,100,255), width=2)

    col_x = [70, 150]
    for x in col_x:
        draw.line([(x, start_y), (x, start_y + row_height * len(SKILL_ORDER) + 1)], fill=(100,100,100,255), width=2)
    draw.line([(10, start_y), (10, start_y + row_height*len(SKILL_ORDER))], fill=(100,100,100,255), width=2)
    draw.line([(width-10, start_y), (width-10, start_y + row_height*len(SKILL_ORDER))], fill=(100,100,100,255), width=2)

    items = inventory.get("items", {})
    tb = next((x for x in inventory.get("inventories", []) if x.get("inventoryName")=="Toolbelt"), {})

    for idx, skill_name in enumerate(SKILL_ORDER, start=1):
        y_top = start_y + (idx-1) * row_height
        y_center = y_top + row_height // 2

        # Number
        num_text = str(idx)
        num_bbox = draw.textbbox((0,0), num_text, font=font_row)
        draw.text(((col_x[0]-10-num_bbox[2])//2, y_center - (num_bbox[3]-num_bbox[1])//2), num_text, font=font_row, fill=constants.FONT_COLOR)

        # Icon
        icon_path = None
        for pocket in tb.get("pockets", []):
            c = pocket.get("contents") or {}
            iid = str(c.get("itemId"))
            itm = items.get(iid, {})
            sid = itm.get("toolSkillId")
            if sid and SKILL.get(sid,"").lower() == skill_name.lower():
                raw_name = itm.get("name","?")
                clean_name = raw_name.replace(" ","").replace("'","").replace("&","").replace("-","")
                candidate = f"C:/bcicons/{clean_name}.png"
                if os.path.exists(candidate):
                    icon_path = candidate
                break

        icon_x_center = (col_x[1]+col_x[0])//2
        if icon_path:
            icon_img = Image.open(icon_path).convert("RGBA")
            icon_img.thumbnail((32,32))
            icon_y = y_center - icon_img.height//2
            img.paste(icon_img, (icon_x_center - icon_img.width//2, icon_y), icon_img)

        # Skill name
        skill_text_bbox = draw.textbbox((0,0), skill_name, font=font_row)
        draw.text((col_x[1]+10, y_center - (skill_text_bbox[3]-skill_text_bbox[1])//2), skill_name, font=font_row, fill=constants.FONT_COLOR)

    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)
    file = discord.File(buffer, filename="skills_dashboard.png")

    if isinstance(ctx_or_interaction, discord.Interaction):
        await ctx_or_interaction.response.send_message(file=file)
    else:
        await ctx_or_interaction.send(file=file)


# -------------------------------------------------
# Single skill panel
# -------------------------------------------------
async def send_skill_panel(ctx_or_interaction, player_data, inventory, skill_name):
    skill_name_lower = skill_name.strip().lower()
    skill_id = next((k for k,v in SKILL.items() if v.lower()==skill_name_lower), None)
    if not skill_id:
        await ctx_or_interaction.send(f"Skill '{skill_name}' not found.")
        return

    stats = get_skill_stats(player_data, skill_id)

    tool_display = "*No Tool*"
    tool_icon_path = None
    tool_rarity_color = (255,255,255,255)
    tb = next((x for x in inventory.get("inventories", []) if x.get("inventoryName")=="Toolbelt"), {})
    items = inventory.get("items", {})

    for pocket in tb.get("pockets", []):
        c = pocket.get("contents") or {}
        iid = str(c.get("itemId"))
        itm = items.get(iid, {})
        sid = itm.get("toolSkillId")
        if sid and SKILL.get(sid,"").lower() == skill_name_lower:
            r = (itm.get("rarityStr") or "common").lower()
            tier = itm.get("tier")
            raw_name = itm.get("name","?")
            tname = f"{raw_name} (T{tier})" if tier is not None else raw_name
            clean_name = raw_name.replace(" ","").replace("'","").replace("&","").replace("-","")
            icon_path = f"C:/bcicons/{clean_name}.png"
            if os.path.exists(icon_path):
                tool_icon_path = icon_path
            tool_display = tname
            tool_rarity_color = RAR.get(r, (255,255,255,255))
            break

    width, height = 300, 180
    img = Image.new("RGBA", (width, height), (25,25,30,255))
    draw = ImageDraw.Draw(img)

    font_title = ImageFont.truetype(constants.FONT_BOLD_PATH, 20)
    font_text  = ImageFont.truetype(constants.FONT_REGULAR_PATH, 14)

    # Title
    title = f"{SKILL[skill_id]}"
    title_bbox = draw.textbbox((0,0), title, font=font_title)
    draw.text(((width-(title_bbox[2]-title_bbox[0])//2), 10), title, font=font_title, fill=constants.FONT_COLOR)

    # Info lines
    lines = [
        f"Tool: {tool_display}",
        f"Level: {stats['level']}",
        f"XP: {stats['xp']:,}",
        f"To Next: {stats['xp_to_next']:,}",
        f"To L{stats['mile']}: {'MAX' if stats['xp_to_mile']==0 else f'{stats['xp_to_mile']:,}'}"
    ]
    y = 45
    for line in lines:
        draw.text((20, y), line, font=font_text, fill=constants.FONT_COLOR)
        y += 25

    # Tool icon
    if tool_icon_path and os.path.exists(tool_icon_path):
        tool_img = Image.open(tool_icon_path).convert("RGBA")
        tool_img.thumbnail((48,48))
        icon_x, icon_y = width - 70, 45
        img.paste(tool_img, (icon_x, icon_y), tool_img)
        draw.rectangle([icon_x-3, icon_y-3, icon_x+tool_img.width+3, icon_y+tool_img.height+3], outline=tool_rarity_color, width=3)

    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)
    file = discord.File(buffer, filename="skill_panel.png")

    if isinstance(ctx_or_interaction, discord.Interaction):
        await ctx_or_interaction.response.send_message(file=file)
    else:
        await ctx_or_interaction.send(file=file)


# -------------------------------------------------
# Skill time estimate
# -------------------------------------------------
async def send_skill_time_image(skill_name, tick, xpt, xp_to_next, xp_to_mile, mile, inventory=None):
    width, height = 200, 150
    top_padding = 20
    line_height = 25
    img = Image.new("RGBA", (width, height), (25,25,30,255))
    draw = ImageDraw.Draw(img)

    font_title = ImageFont.truetype(constants.FONT_BOLD_PATH, 18)
    font_text  = ImageFont.truetype(constants.FONT_REGULAR_PATH, 14)

    # Title
    title_text = "Time Estimate"
    title_bbox = draw.textbbox((0,0), title_text, font=font_title)
    draw.text(((width-(title_bbox[2]-title_bbox[0])//2), top_padding), title_text, font=font_title, fill=constants.FONT_COLOR)

    y = top_padding + title_bbox[3] + 10
    draw.text((20, y), f"Tick: {tick}s", font=font_text, fill=constants.FONT_COLOR); y += line_height
    draw.text((20, y), f"XP/Tick: {xpt}", font=font_text, fill=constants.FONT_COLOR); y += line_height
    draw.text((20, y), f"To Next: {dhm(int(xp_to_next*1000))}", font=font_text, fill=constants.FONT_COLOR); y += line_height
    draw.text((20, y), f"To L{mile}: {dhm(int(xp_to_mile*1000))}", font=font_text, fill=constants.FONT_COLOR); y += line_height

    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)
    return buffer

async def _skill_command(ctx_or_interaction, user_id, *, ephemeral=False):
    """
    Internal logic for skill command.
    ctx_or_interaction: discord.Context or discord.Interaction
    user_id: ID of the user
    ephemeral: relevant for slash commands only
    """
    # Check if character is set
    p = last_char.get(user_id)
    if not p:
        msg = "`!setchar` first." if isinstance(ctx_or_interaction, commands.Context) else "`/setchar` first."
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(msg)
        else:
            await ctx_or_interaction.response.send_message(msg, ephemeral=ephemeral)
        return

    # Fetch player data and inventory
    player_data = player(p["id"])
    inventory = inv(p["id"])

    # Send dashboard
    await send_skills_dashboard(ctx_or_interaction, player_data, inventory)

    # Wait for skill selection
    def check(m):
        return m.author.id == user_id and m.channel == getattr(ctx_or_interaction, "channel", None)

    try:
        msg = await ctx_or_interaction.bot.wait_for("message", check=check, timeout=60)
        choice = int(msg.content.strip())
        if not 1 <= choice <= len(constants.SKILL_ORDER):
            raise ValueError
    except asyncio.TimeoutError:
        text = "Timeout. Cancelled."
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(text)
        else:
            await ctx_or_interaction.followup.send(text, ephemeral=ephemeral)
        return
    except ValueError:
        text = "Invalid selection. Cancelled."
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(text)
        else:
            await ctx_or_interaction.followup.send(text, ephemeral=ephemeral)
        return

    skill_name = constants.SKILL_ORDER[choice - 1]

    # Show skill panel
    await send_skill_panel(ctx_or_interaction, player_data, inventory, skill_name)

    # Ask if time estimate is desired
    prompt_text = "Estimate time? Type `yes` within 60s to proceed."
    if isinstance(ctx_or_interaction, commands.Context):
        await ctx_or_interaction.send(prompt_text)
    else:
        await ctx_or_interaction.followup.send(prompt_text, ephemeral=ephemeral)

    try:
        msg = await ctx_or_interaction.bot.wait_for("message", check=check, timeout=60)
        if msg.content.lower() not in ("yes", "y"):
            text = "Skipped."
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send(text)
            else:
                await ctx_or_interaction.followup.send(text, ephemeral=ephemeral)
            return
    except asyncio.TimeoutError:
        # Default tick and XP
        tick, xpt = 60.0, 1.0
    else:
        # Ask for tick and XP
        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send("Tick length (seconds):")
        else:
            await ctx_or_interaction.followup.send("Tick length (seconds):", ephemeral=ephemeral)

        try:
            tick = float((await ctx_or_interaction.bot.wait_for("message", check=check, timeout=60)).content)
        except:
            tick = 60.0

        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send("XP per tick:")
        else:
            await ctx_or_interaction.followup.send("XP per tick:", ephemeral=ephemeral)

        try:
            xpt = float((await ctx_or_interaction.bot.wait_for("message", check=check, timeout=60)).content)
        except:
            xpt = 1.0

        if tick <= 0 or xpt <= 0:
            text = "Values must be > 0."
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send(text)
            else:
                await ctx_or_interaction.followup.send(text, ephemeral=ephemeral)
            return

    # Compute XP times
    stats = get_skill_stats(player_data, next(k for k,v in SKILL.items() if v.lower() == skill_name.lower()))
    xp_to_next = stats['xp_to_next']
    xp_to_mile = stats['xp_to_mile']
    mile = stats['mile']

    t_next = (xp_to_next / xpt) * tick if xp_to_next > 0 else 0
    t_mile = (xp_to_mile / xpt) * tick if xp_to_mile > 0 else 0

    # Generate time estimate image
    buffer = await send_skill_time_image(
        skill_name=skill_name,
        tick=tick,
        xpt=xpt,
        xp_to_next=t_next,
        xp_to_mile=t_mile,
        mile=mile,
        inventory=inventory
    )

    file = discord.File(buffer, filename="skill_time.png")
    if isinstance(ctx_or_interaction, commands.Context):
        await ctx_or_interaction.send(file=file)
    else:
        await ctx_or_interaction.followup.send(file=file)
