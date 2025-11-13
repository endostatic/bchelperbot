#---------------------------
# Developer Helper
#---------------------------
import discord
import asyncio
import importlib
from discord.ext import commands
import helpers
import constants
import skillpillow
import commands as bot_commands
import sys  # Added to fix reload_module reference

# -------------------------------------------------
# Helper: Reload a specific module
# -------------------------------------------------
async def reload_module(ctx, module_name: str):
    """
    Reload a single module.
    Developer-only output remains direct; no Pillow conversion required.
    """
    try:
        module = sys.modules.get(module_name)
        if not module:
            await ctx.send(f"❌ Module `{module_name}` not found.")
            return
        importlib.reload(module)
        await ctx.send(f"✅ Reloaded `{module_name}` successfully.")
    except Exception as e:
        await ctx.send(f"❌ Failed to reload `{module_name}`: {type(e).__name__} - {e}")

# -------------------------------------------------
# Reload All Core Modules
# -------------------------------------------------
async def reload_all(ctx):
    """
    Reload all core modules.
    Developer-only output remains direct; no Pillow conversion required.
    """
    modules = [constants, helpers, skillpillow, bot_commands]
    reloaded, failed = [], []
    for module in modules:
        try:
            importlib.reload(module)
            reloaded.append(module.__name__)
        except Exception as e:
            failed.append((module.__name__, str(e)))
    summary = ""
    if reloaded:
        summary += f"✅ Reloaded: {', '.join(reloaded)}\n"
    if failed:
        summary += f"❌ Failed:\n" + "\n".join([f"- {m}: {e}" for m, e in failed])
    await ctx.send(summary or "No modules were reloaded.")

# -------------------------------------------------
# Reload Helpers Only
# -------------------------------------------------
async def reload_helpers(ctx):
    """
    Reload only helpers.py.
    Developer-only output remains direct; no Pillow conversion required.
    """
    try:
        importlib.reload(helpers)
        await ctx.send("✅ `helpers.py` reloaded successfully.")
    except Exception as e:
        await ctx.send(f"❌ Failed to reload helpers.py: {type(e).__name__} - {e}")

#-------------------------------------------------------
# Future commands printed here to be moved later
#-------------------------------------------------------
# -------------------------------------------------
# !skillgrid – shows XP *remaining* to next level & milestone
# -------------------------------------------------
@bot.command()
async def skillgrid(ctx):
    p = last_char.get(ctx.author.id)
    if not p: return await ctx.send("`!setchar` first.")
    pd, i = player(p["id"]), inv(p["id"])
    tools = {}
    tb = next((x for x in i.get("inventories",[]) if x.get("inventoryName")=="Toolbelt"), {})
    items = i.get("items", {})
    for pocket in tb.get("pockets", []):
        c = pocket.get("contents") or {}
        iid = str(c.get("itemId"))
        itm = items.get(iid, {})
        sid = itm.get("toolSkillId")
        if not sid: continue
        sname = SKILL.get(sid)
        if sname in GRID and sname not in tools:
            r = (itm.get("rarityStr") or "common").lower()
            tier = itm.get("tier")
            name = f"{itm.get('name','?')} (T{tier})" if tier is not None and tier>=0 else itm.get("name","?")
            tools[sname] = (name, f":{RAR.get(r, 'white_circle:')}:")
    e = discord.Embed(title="Skill Grid", color=0x1E90FF)
    for s in GRID:
        sid = next((int(k) for k,v in pd.get("skillMap",{}).items() if v["name"]==s), None)
        if not sid: continue
        xp = next((e["quantity"] for e in pd.get("experience",[]) if e["skill_id"]==sid), 0)

        # ---- calculate remaining XP ----
        level = 1
        for l in range(1, 101):
            if xp < LEVEL_XP.get(l + 1, float('inf')):
                level = l
                break
        xp_to_next = LEVEL_XP.get(level + 1, float('inf')) - xp
        mile = min(((level // 10) + 1) * 10, 100)
        xp_to_mile = LEVEL_XP[mile] - xp if mile <= 100 and xp < LEVEL_XP[mile] else 0
        name, emoji = tools.get(s, ("*None*", ":white_circle:"))
        e.add_field(
            name=s,
            value=f"{emoji} {name}\n"
                  f"🎖 Lvl: {level}\n"
                  f"📊 XP: {xp:,}\n"
                  f"⏫ Next: {xp_to_next:,}\n"         # ← XP *remaining* to next level
                  f"🏆 L{mile}: {'MAX' if xp_to_mile==0 else f'{xp_to_mile:,}'}",
            inline=True
        )
    await ctx.send(embed=e)

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

@bot.command()
async def tskillgrid(ctx):
    p = last_char.get(ctx.author.id)
    if not p:
        return await ctx.send("`!setchar` first.")

    pd, i = player(p["id"]), inv(p["id"])
    tools = {}
    tb = next((x for x in i.get("inventories", []) if x.get("inventoryName") == "Toolbelt"), {})
    items = i.get("items", {})

    # Gather tools and their icons
    for pocket in tb.get("pockets", []):
        c = pocket.get("contents") or {}
        iid = str(c.get("itemId"))
        itm = items.get(iid, {})
        sid = itm.get("toolSkillId")
        if not sid:
            continue

        sname = SKILL.get(sid)
        if sname in GRID and sname not in tools:
            r = (itm.get("rarityStr") or "common").lower()
            tier = itm.get("tier")
            raw_name = itm.get("name", "?")
            tname = f"{raw_name} (T{tier})" if tier is not None and tier >= 0 else raw_name

            clean_name = raw_name.replace(" ", "").replace("'", "").replace("&", "").replace("-", "")
            icon_path = f"C:/bcicons/{clean_name}.png"

            rarity_emoji = f":{RAR.get(r, 'white_circle:')}:"
            tools[sname] = {
                "name": tname,
                "emoji": rarity_emoji,
                "icon": icon_path if os.path.exists(icon_path) else None,
                "power": int(itm.get("toolPower", 1))
            }

    sorted_grid = sorted(GRID)
    skills_to_display = sorted_grid[:12]  # First 12 skills

    # --- Pillow grid settings ---
    panel_width, panel_height = 200, 150
    cols, rows = 3, 2
    font = ImageFont.truetype("arial.ttf", 14)
    title_font = ImageFont.truetype("arialbd.ttf", 16)

    # Split into two pages (3x2 each)
    for page in range(2):
        grid_img = Image.new("RGBA", (panel_width * cols, panel_height * rows), (30, 30, 30, 255))
        draw_grid = ImageDraw.Draw(grid_img)

        for idx in range(page * 6, min((page + 1) * 6, len(skills_to_display))):
            s = skills_to_display[idx]
            sid = next((int(k) for k, v in pd.get("skillMap", {}).items() if v["name"] == s), None)
            if not sid:
                continue

            xp = next((ex["quantity"] for ex in pd.get("experience", []) if ex["skill_id"] == sid), 0)
            level = 1
            for l in range(1, 101):
                if xp < LEVEL_XP.get(l + 1, float('inf')):
                    level = l
                    break
            xp_to_next = LEVEL_XP.get(level + 1, float('inf')) - xp
            mile = min(((level // 10) + 1) * 10, 100)
            xp_to_mile = LEVEL_XP[mile] - xp if mile <= 100 and xp < LEVEL_XP[mile] else 0

            tool = tools.get(s)
            icon_img = None
            if tool and tool["icon"] and os.path.exists(tool["icon"]):
                icon_img = Image.open(tool["icon"]).convert("RGBA").resize((64, 64))

            # --- Draw panel background ---
            panel = Image.new("RGBA", (panel_width, panel_height), (50, 50, 50, 255))
            panel_draw = ImageDraw.Draw(panel)

            # Draw icon
            if icon_img:
                icon_img = icon_img.resize((32, 32))
                icon_x = panel_width - 32 - 5  # 5px padding from right edge
                icon_y = 5  # 5px padding from top
                panel.paste(icon_img, (icon_x, icon_y), icon_img)

            # Starting X for all text (leave space on right for icon)
            text_x = 10
            text_y = 5

            # Skill title
            panel_draw.text((text_x, text_y), s, font=title_font, fill=(255, 255, 255, 255))

            # Tool name + emoji
            panel_draw.text((text_x, text_y + 25), f"{tool['emoji']} {tool['name']}" if tool else "*No Tool*", 
                font=font, fill=(255, 255, 255, 255))

            # Stats (stack vertically)
            panel_draw.text((text_x, text_y + 50), f"Lvl: {level}", font=font, fill=(200, 200, 200, 255))
            panel_draw.text((text_x, text_y + 70), f"XP: {xp:,}", font=font, fill=(200, 200, 200, 255))
            panel_draw.text((text_x, text_y + 90), f"Next: {xp_to_next:,}", font=font, fill=(200, 200, 200, 255))
            panel_draw.text((text_x, text_y + 110), f"L{mile}: {'MAX' if xp_to_mile==0 else f'{xp_to_mile:,}'}",
                font=font, fill=(200, 200, 200, 255))


            # Paste panel into grid
            col = (idx % 6) % cols
            row = (idx % 6) // cols
            grid_img.paste(panel, (col * panel_width, row * panel_height))

        # Save image to BytesIO
        bio = BytesIO()
        grid_img.save(bio, format="PNG")
        bio.seek(0)

        await ctx.send(file=discord.File(bio, filename=f"skillgrid_page{page+1}.png"))




      
# -------------------------------------------------
# equipment - Show current equipment for selected character
# ------------------------------------------------- 

@bot.command()
async def equipment(ctx):
    p = last_char.get(ctx.author.id)
    if not p: return await ctx.send("`!setchar` first.")
    eid = p["id"]
    u = player(eid).get("username", "Unknown")
    data = api(f"https://bitjita.com/api/players/{eid}/equipment")

    equipped = []
    for entry in data.get("equipment", []):
        item = entry.get("item")
        if not item: continue

        # ---- Rarity from item["rarityString"] (exact key from JSON) ----
        rarity_raw = item.get("rarityString")
        rarity = (rarity_raw or "Common").strip().lower() if rarity_raw else "common"
        emoji = f":{RAR.get(rarity, 'white_circle:')}:"

        name = item.get("name", "Unknown")
        slot = SLOT.get(entry["primary"], entry["primary"].replace("_", " ").title())

        equipped.append((slot, f"{emoji} {name}"))

    if not equipped:
        return await ctx.send(f"**{u}** has no gear.")

    e = discord.Embed(title=f"{u} – Equipment", color=0x1E90FF)
    for i in range(0, len(equipped), 3):
        for s, n in equipped[i:i+3]:
            e.add_field(name=f"**{s}**", value=n, inline=True)
        for _ in range(3 - len(equipped[i:i+3])):
            e.add_field(name="\u200b", value="\u200b", inline=True)

    await ctx.send(embed=e)

# -------------------------------------------------
# watchtowers - Check timers for watchtowers and claim on demand
# -------------------------------------------------
@bot.command()
async def watchtowers(ctx, *, name=None):
    try:
        if not name:
            name = last_emp.get(ctx.author.id) or last_clm.get(ctx.author.id)
            if not name: return await ctx.send("Use `!watchtowers <Empire>` or `<Claim>` first.")

        force_empire = " empire" in name.lower()
        force_claim = " claim" in name.lower()
        if force_empire or force_claim:
            name = name.rsplit(" ", 1)[0].strip()

        # ---- Step 1: Try exact match (Empire) ----
        if not force_claim:
            e = api(f"https://bitjita.com/api/empires?q={name}").get("empires", [])
            if e:
                emp = e[0]; eid = emp["entityId"]; en = emp.get("name", name)
                lines = []
                for t in api(f"https://bitjita.com/api/empires/{eid}/towers"):
                    n = t.get("nickname","?")
                    x,z = t.get("locationX",0), t.get("locationZ",0)
                    timer = dhm(int(t["energy"]/max(t.get("upkeep",1),1)*3600000)) if t.get("active") and t.get("energy",0)>0 else "Inactive"
                    n_coord, e_coord = ne(x, z)
                    lines.append(f"**{n}**: {timer} | **{n_coord}N, {e_coord}E**")
                if (cid:=emp.get("capitalClaimId")):
                    c = claim_data(cid)
                    sup, base = c.get("supplies",0), c.get("upkeepCost",0)
                    timer = dhm(int(sup/max(base-1.15,0)*3600000)) if base>1.15 else "Infinity"
                    lines.append(f"**{c.get('name','Capital')} Supplies**: {sup:,} to {timer}")
                last_emp[ctx.author.id] = name
                return await ctx.send(embed=discord.Embed(title=f"{en} – Watchtowers", description="\n".join(lines), color=0xFF7518).set_footer(text="Empire • Live"))

        # ---- Step 2: Try exact match (Claim) ----
        if not force_empire:
            c = claim(name)
            if c:
                cd = claim_data(c[0]["entityId"])
                sup, base = cd.get("supplies",0), cd.get("upkeepCost",0)
                timer = dhm(int(sup/max(base-1.15,0)*3600000)) if base>1.15 else "Infinity"
                last_clm[ctx.author.id] = name
                await ctx.send(embed=discord.Embed(title=f"Claim: {cd.get('name',name)} (Independent)", description=f"**Claim Supplies**: {sup:,} to {timer}", color=0xFF7518).set_footer(text="Claim • Live"))
                return

        # ---- Step 3: No exact match → fuzzy suggest by first 3 chars ----
        prefix = name[:3].lower()
        all_empires = api("https://bitjita.com/api/empires").get("empires", [])
        empire_matches = [e for e in all_empires if e.get("name", "").lower().startswith(prefix)]
        all_claims = api(f"https://bitjita.com/api/claims?q={prefix}").get("claims", [])
        claim_matches = [cl for cl in all_claims if cl.get("name", "").lower().startswith(prefix)]

        suggestions = []
        for i, e in enumerate(empire_matches[:3]):
            suggestions.append((i+1, e["name"], "Empire"))
        for i, cl in enumerate(claim_matches[:3]):
            suggestions.append((i+1 + len(empire_matches), cl["name"], "Claim"))

        if not suggestions:
            return await ctx.send(f"**{name}** not found and no suggestions.")

        lines = [f"{num}.) **{n}** ({typ})" for num, n, typ in suggestions]
        await ctx.send(f"Did you mean:\n" + "\n".join(lines) + "\n\nMake a selection:")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit() and 1 <= int(m.content) <= len(suggestions)

        try:
            reply = await bot.wait_for("message", check=check, timeout=60)
            idx = int(reply.content) - 1
            selected_name, selected_type = suggestions[idx][1], suggestions[idx][2]
        except asyncio.TimeoutError:
            return await ctx.send("Timed out – no selection.")

        # ---- Step 4: Execute selected ----
        if selected_type == "Empire":
            e = [x for x in all_empires if x["name"] == selected_name][0]
            eid = e["entityId"]; en = e.get("name", selected_name)
            lines = []
            for t in api(f"https://bitjita.com/api/empires/{eid}/towers"):
                n = t.get("nickname","?")
                x,z = t.get("locationX",0), t.get("locationZ",0)
                timer = dhm(int(t["energy"]/max(t.get("upkeep",1),1)*3600000)) if t.get("active") and t.get("energy",0)>0 else "Inactive"
                n_coord, e_coord = ne(x, z)
                lines.append(f"**{n}**: {timer} | **{n_coord}N, {e_coord}E**")
            if (cid:=e.get("capitalClaimId")):
                c = claim_data(cid)
                sup, base = c.get("supplies",0), c.get("upkeepCost",0)
                timer = dhm(int(sup/max(base-1.15,0)*3600000)) if base>1.15 else "Infinity"
                lines.append(f"**{c.get('name','Capital')} Supplies**: {sup:,} to {timer}")
            last_emp[ctx.author.id] = selected_name
            await ctx.send(embed=discord.Embed(title=f"{en} – Watchtowers", description="\n".join(lines), color=0xFF7518).set_footer(text="Empire • Live"))
        else:
            c = [x for x in all_claims if x["name"] == selected_name][0]
            cd = claim_data(c["entityId"])
            sup, base = cd.get("supplies",0), cd.get("upkeepCost",0)
            timer = dhm(int(sup/max(base-1.15,0)*3600000)) if base>1.15 else "Infinity"
            last_clm[ctx.author.id] = selected_name
            await ctx.send(embed=discord.Embed(title=f"Claim: {cd.get('name',selected_name)} (Independent)", description=f"**Claim Supplies**: {sup:,} to {timer}", color=0xFF7518).set_footer(text="Claim • Live"))

    except Exception as e:
        await ctx.send(f"Error: {e}")
    
# -------------------------------------------------
# setempire - Choose an empire to monitor
# -------------------------------------------------

@bot.command()
async def setempire(ctx, *, name=None):
    if not name:
        return await ctx.send("`!setempire EmpireName`")

    channel_id = ctx.channel.id
    user_id = ctx.author.id

    # Cancel any existing monitor for this user
    if user_id in user_empire_monitor:
        user_empire_monitor[user_id]["task"].cancel()
        await ctx.send("Replaced previous empire monitor.")

    # ---- Step 1: Try exact match ----
    exact = api(f"https://bitjita.com/api/empires?q={name}").get("empires", [])
    if exact:
        emp = exact[0]
        eid = emp["entityId"]
        en = emp.get("name", name)
        await ctx.send(f"Monitoring **{en}** | Towers ≤24h | Capital ≤72h")
        task = asyncio.create_task(monitor_empire(ctx.channel, eid, en))
        user_empire_monitor[user_id] = {
            "task": task,
            "eid": eid,
            "name": en,
            "alerts": {},
            "channel_id": channel_id  # Remember where to send alerts
        }
        return

    # ---- Step 2: No exact match → fuzzy suggest by first 3 chars ----
    prefix = name[:3].lower()
    all_empires = api("https://bitjita.com/api/empires").get("empires", [])
    matches = [e for e in all_empires if e.get("name", "").lower().startswith(prefix)]
    if not matches:
        return await ctx.send(f"Empire **{name}** not found and no suggestions.")

    suggestions = matches[:3]
    lines = [f"{i+1}.) **{s['name']}**" for i, s in enumerate(suggestions)]
    await ctx.send(f"Did you mean:\n" + "\n".join(lines) + "\n\nMake a selection:")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content in ("1", "2", "3")

    try:
        reply = await bot.wait_for("message", check=check, timeout=60)
        idx = int(reply.content) - 1
        if idx >= len(suggestions):
            return await ctx.send("Invalid selection.")
        selected = suggestions[idx]
    except asyncio.TimeoutError:
        return await ctx.send("Timed out – no empire selected.")

    # ---- Step 3: Proceed with selected empire ----
    eid = selected["entityId"]
    en = selected.get("name", name)
    await ctx.send(f"Monitoring **{en}** | Towers ≤24h | Capital ≤72h")
    task = asyncio.create_task(monitor_empire(ctx.channel, eid, en))
    user_empire_monitor[user_id] = {
        "task": task,
        "eid": eid,
        "name": en,
        "alerts": {},
        "channel_id": channel_id
    }