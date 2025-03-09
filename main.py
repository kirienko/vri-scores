import discord
import aiohttp
from extract import extract_rankings_from_bytes

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_message(message):
    # Ignore messages from bots
    if message.author.bot:
        return

    # If the message has attachments
    if message.attachments:
        images = []
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status == 200:
                            images.append(await resp.read())

        if images:
            rankings_all = {}
            for img_bytes in images:
                ranking = extract_rankings_from_bytes(img_bytes)
                rankings_all.update(ranking)  # Assuming no rank conflicts

            if rankings_all:
                sorted_ranks = sorted(rankings_all.keys())
                result = "\n".join(f"{rank} {rankings_all[rank]}" for rank in sorted_ranks)
                await message.reply(f"**Ranking:**\n{result}")
            else:
                await message.reply("No rankings detected.")

with open("token.txt", "r") as f:
    token = f.read().strip()
client.run(token)
