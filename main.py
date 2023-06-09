import asyncio
import os
import re
import traceback
import zipfile
from io import BytesIO

import aiohttp
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


def list_chunk(lst, n):
    return [lst[i : i + n] for i in range(0, len(lst), n)]


async def request(session: aiohttp.ClientSession, data: dict):
    buf = BytesIO()

    async with session.get(data["url"]) as response:
        buf.write(await response.read())

    buf.seek(0)

    return {
        "filename": f"{data['name']}.{data['ext']}",
        "content": buf,
    }


async def load_images(data: list):
    files = []

    for idx, chunk in enumerate(list_chunk(data, 50)):
        print(f"Chunk {idx + 1} / {len(data) // 50 + 1}")
        async with aiohttp.ClientSession() as session:
            tasks = [request(session, x) for x in chunk]
            files.extend(await asyncio.gather(*tasks))

    zip_buffer = BytesIO()

    with zipfile.ZipFile(
        zip_buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as zip_file:
        for file in files:
            zip_file.writestr(file["filename"], file["content"].getvalue())

    zip_buffer.seek(0)

    return zip_buffer


@bot.command("이모지")
@commands.has_guild_permissions(administrator=True)
async def emoji(ctx: commands.Context):
    msg = await ctx.reply("잠시만 기다려 주세요!")

    try:
        emojis = ctx.guild.emojis

        zip_buffer = await load_images(
            [
                {
                    "url": emoji.url,
                    "name": emoji.name,
                    "ext": "gif" if emoji.animated else "png",
                }
                for emoji in emojis
            ]
        )

        await ctx.send(file=discord.File(zip_buffer, "emojis.zip"))
        await msg.delete()
    except:
        await msg.edit(content="오류가 발생했습니다!")
        traceback.print_exc()


@bot.command("스티커")
@commands.has_guild_permissions(administrator=True)
async def sticker(ctx: commands.Context):
    msg = await ctx.reply("잠시만 기다려 주세요!")

    try:
        stickers = ctx.guild.stickers

        zip_buffer = await load_images(
            [
                {
                    "url": sticker.url,
                    "name": sticker.name,
                    "ext": sticker.format.file_extension,
                }
                for sticker in stickers
            ]
        )

        await ctx.send(file=discord.File(zip_buffer, "stickers.zip"))
        await msg.delete()
    except:
        await msg.edit(content="오류가 발생했습니다!")
        traceback.print_exc()


bot.run(os.getenv("TOKEN"))
