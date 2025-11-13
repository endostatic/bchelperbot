#-----------------------
# Bot Helper Functions
#-----------------------
import discord
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
from discord.ext import commands
import constants, skillpillow, dev

user_characters = {}

def set_user_character(user_id, character_name):
    user_characters[user_id] = character_name

def get_user_character(user_id):
    return user_characters.get(user_id)

# -------------------------------------------------
# API Wrappers
# -------------------------------------------------
def api(url, timeout=10):
    try:
        return requests.get(url, timeout=timeout).json()
    except:
        return {}

def player(entity_id):
    return api(f"https://bitjita.com/api/players/{entity_id}").get("player", {})

def inv(entity_id):
    return api(f"https://bitjita.com/api/players/{entity_id}/inventories")

def claim(player_id):
    return api(f"https://bitjita.com/api/claims?q={player_id}").get("claims", [])

def claim_data(claim_id):
    return api(f"https://bitjita.com/api/claims/{claim_id}").get("claim", {})

# -------------------------------------------------
# Utility functions
# -------------------------------------------------
def ne(x, z):
    return round(z / 3), round(x / 3)

def dhm(ms):
    if ms <= 0:
        return "0m"
    s = ms // 1000
    d = s // 86400
    h = s % 86400 // 3600
    m = s % 3600 // 60
    return " ".join(filter(None, [f"{d}d" if d else "", f"{h}h" if h else "", f"{m}m" if m else ""])) or "0m"

def get_level(xp, level_xp):
    """Return level, XP into current level, and XP to next level."""
    for l in range(1, 101):
        if xp < level_xp.get(l + 1, float('inf')):
            return l, xp - level_xp[l], level_xp.get(l + 1, float('inf')) - level_xp[l]
    return 100, 0, 0

# -------------------------------------------------
# Pillow helpers (general)
# -------------------------------------------------
DEFAULT_COLOR = constants.FONT_COLOR
FONT_PATH_BOLD = constants.FONT_BOLD_PATH
FONT_PATH_REGULAR = constants.FONT_REGULAR_PATH

def load_font_bold(size=constants.FONT_SIZE_TITLE):
    return ImageFont.truetype(FONT_PATH_BOLD, size)

def load_font_regular(size=constants.FONT_SIZE_DEFAULT):
    return ImageFont.truetype(FONT_PATH_REGULAR, size)

def create_basic_image(width, height, background=(0, 0, 0, 1)):
    return Image.new("RGBA", (width, height), background)

def draw_centered_text(draw, text, x_center, y, font, fill=DEFAULT_COLOR):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    draw.text((x_center - text_width // 2, y), text, font=font, fill=fill)

def save_image_to_bytesio(img):
    buffer = BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)
    return buffer

# -------------------------------------------------
# Centralized Pillow Output Helper
# -------------------------------------------------
async def send_pillow_text(ctx, text, width=450, height=80, font_size=14):
    """Send any text message via Pillow to enforce Lexend font and color."""
    img = Image.new("RGBA", (width, height), (30,30,35,255))
    draw = ImageDraw.Draw(img)
    font = load_font_regular(font_size)

    # Center text
    bbox = draw.textbbox((0,0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    draw.text((x, y), text, font=font, fill=DEFAULT_COLOR)

    # Convert to BytesIO
    buffer = BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)

    # Send via Discord
    await ctx.send(file=discord.File(fp=buffer, filename="output.png"))

async def send_commands_dashboard(ctx_or_interaction): 
    commands_list = [
        ("!setchar <Player>", "Set your character"),
        ("!skill <Skill>", "XP, level, time estimate"),
        ("!skillgrid", "All skills + tools"),
        ("!equipment", "Equipped gear"),
        ("!watchtowers <Empire/Claim>", "On-demand check"),
        ("!setempire <Empire>", "Start live monitor"),
        ("!commands", "This list")
    ]

    # Image dimensions
    width = 450
    top_padding = 40
    line_height = 30
    bottom_padding = 20
    height = top_padding + len(commands_list) * line_height + bottom_padding

    # Create the image
    img = Image.new("RGBA", (width, height), (0, 0, 0, 1))
    draw = ImageDraw.Draw(img)

    # Fonts
    font_title   = ImageFont.truetype(constants.FONT_BOLD_PATH, 18)
    font_command = ImageFont.truetype(constants.FONT_REGULAR_PATH, 12)

    # Draw title
    title_text = "BitCraft Bot Commands"
    title_bbox = font_title.getbbox(title_text)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((width - title_width) / 2, 10), title_text, font=font_title, fill=constants.FONT_COLOR)

    # Draw commands
    y_offset = top_padding
    for i, (cmd, desc) in enumerate(commands_list):
        draw.line([(10, y_offset - 5), (width - 10, y_offset - 5)], fill=(80, 80, 80, 255))
        draw.text((20, y_offset), cmd, font=font_command, fill=constants.FONT_COLOR)
        draw.text((260, y_offset), desc, font=font_command, fill=constants.FONT_COLOR)
        y_offset += line_height
    draw.line([(10, y_offset - 10), (width - 10, y_offset - 10)], fill=(80, 80, 80, 255))

    # Convert to BytesIO for sending
    buffer = BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)
    file = discord.File(fp=buffer, filename="commands.png")

    if isinstance(ctx_or_interaction, discord.Interaction):
        await ctx_or_interaction.response.send_message(file=file)
    else:
        await ctx_or_interaction.send(file=file)
