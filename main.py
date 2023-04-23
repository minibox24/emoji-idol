import os
import re

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


@bot.event
async def on_ready():
    await bot.load_extension("jishaku")

    print(f"Logged in as {bot.user}")


@bot.listen("on_message")
async def on_message(message: discord.Message):
    if not isinstance(message.author, discord.Member):
        return

    if message.author.guild_permissions.administrator:
        return

    if message.content:
        if not re.match(r"^(\s|<a?:\w+:\d+>)+$", message.content):
            await message.delete()


bot.run(os.getenv("TOKEN"))
