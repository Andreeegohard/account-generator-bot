import os
import discord
from discord.ext import commands
import random
import aiohttp
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')

# Load config from config.json
with open('config.json', 'r') as f:
    config = json.load(f)

webhook_url = config['webhook_url']
bot_token = config['bot_token']

# Dictionary to hold different types of passwords
password_dict = {}

# Function to load passwords from files
def load_passwords():
    global password_dict
    password_dict.clear()
    password_files = os.listdir("passwords")
    for file_name in password_files:
        with open(os.path.join("passwords", file_name), "r") as f:
            password_type = os.path.splitext(file_name)[0]
            password_dict[password_type] = f.readlines()

# Command cooldown
cooldown = commands.CooldownMapping.from_cooldown(1, 60.0, commands.BucketType.user)

# Initialize bot and set command prefix
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Command to generate passwords
@bot.command()
@commands.cooldown(1, 60.0, commands.BucketType.user)
async def gen(ctx, pass_type: str):
    """Generate a password of a specific type with a cooldown of 1 minute."""
    if pass_type in password_dict:
        if len(password_dict[pass_type]) > 0:
            random_pass = random.choice(password_dict[pass_type])
            password_dict[pass_type].remove(random_pass)
            with open(os.path.join("passwords", f"{pass_type}.txt"), "w") as f:
                f.writelines(password_dict[pass_type])
            embed = discord.Embed(title="Generated Password", description=random_pass.strip(), color=0x00ff00)
            await ctx.send(embed=embed)

            # Logging via webhook
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(webhook_url, adapter=discord.AsyncWebhookAdapter(session))
                await webhook.send(f'Password generated for {pass_type} by {ctx.author.display_name} in {ctx.channel.name}', username='Password Generator Bot')

        else:
            await ctx.send("No more passwords available for this type.")
    else:
        await ctx.send("Invalid password type.")

# Command to add new types of passwords
@bot.command()
@commands.has_permissions(administrator=True)
async def addpass(ctx, pass_type: str):
    """Add a new type of password (admin only)."""
    if pass_type not in password_dict:
        password_dict[pass_type] = []
        with open(os.path.join("passwords", f"{pass_type}.txt"), "w") as f:
            f.write("defaultpassword1\n")  # Default password
        await ctx.send(f"New password type '{pass_type}' added.")
    else:
        await ctx.send("Password type already exists.")

# Command to list available password types and counts as embed
@bot.command()
async def passwords(ctx):
    """List available password types and their counts."""
    embed = discord.Embed(title="Available Password Types", color=0xffd700)
    for pass_type, pass_list in password_dict.items():
        embed.add_field(name=pass_type, value=f"Count: {len(pass_list)}", inline=False)
    await ctx.send(embed=embed)

# Command to display list of commands and their usage
@bot.command()
async def commands_help(ctx):
    """Display list of available commands."""
    embed = discord.Embed(title="Available Commands", color=0x00ff00)
    embed.add_field(name="!gen {type}", value="Generate a password of a specific type.", inline=False)
    embed.add_field(name="!passwords", value="List available account types and their counts.", inline=False)
    embed.add_field(name="!addpass {type}", value="Add a new type of password (admin only).", inline=False)
    await ctx.send(embed=embed)

# Load passwords when bot starts
@bot.event
async def on_ready():
    print('Bot is ready.')
    load_passwords()

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f'This command is on cooldown. Please try again in {error.retry_after:.0f} seconds.')
    else:
        logger.error(error)

bot.run(bot_token)
