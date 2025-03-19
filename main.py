import discord
import aiohttp
import pandas as pd
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


# Mapping for digit emoji (and optionally the "ten" emoji)
emoji_to_int = {
    "0️⃣": 0,
    "1️⃣": 1,
    "2️⃣": 2,
    "3️⃣": 3,
    "4️⃣": 4,
    "5️⃣": 5,
    "6️⃣": 6,
    "7️⃣": 7,
    "8️⃣": 8,
    "9️⃣": 9,
    "🔟": 10,
}

race_table = pd.DataFrame(columns=["Participant", "Total"])
# reset the index and add 1 to each value
race_table.index = race_table.index + 1

@client.event
async def on_reaction_add(reaction, user):
    # If the reaction is on a message with attachments
    if reaction.message.attachments:
        print("trying to recognize a reaction")
        race_number = emoji_to_int.get(reaction.emoji)
        if race_number is not None:
            print(f"The race number {race_number}")
            images = []
            for attachment in reaction.message.attachments:
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
                    # Determine the ordering for this race
                    race_order = sorted(rankings_all.keys())
                    race_participant_count = len(race_order)
                    new_race = {}
                    for pos in race_order:
                        participant = rankings_all[pos]
                        new_race[participant] = pos
                    global race_table
                    # Ensure all participants in this race are present in the table
                    for participant in new_race:
                        if participant not in race_table["Participant"].values:
                            race_table = pd.concat([race_table, pd.DataFrame({"Participant": [participant]})], ignore_index=True)
                    # New column corresponding to this race number
                    column_label = str(race_number)
                    default_points = race_participant_count + 1
                    for idx, row in race_table.iterrows():
                        pname = row["Participant"]
                        race_table.at[idx, column_label] = new_race.get(pname, default_points)
                    # Recalculate Total: sum over all race columns (excluding Participant and Total)
                    race_cols = [col for col in race_table.columns if col not in ["Participant", "Total"]]
                    race_table[race_cols] = race_table[race_cols].astype(int)
                    race_table["Total"] = race_table[race_cols].sum(axis=1)
                    print("Updated race table:")
                    print(race_table)
                    try:
                        table_md = race_table.to_markdown()
                    except ImportError:
                        table_md = race_table.to_string()
                    await reaction.message.reply(f"**Overall:**\n{table_md}")
                else:
                    print("No rankings detected in images.")
            else:
                print("No images to process for ranking.")
        else:
            print(f"unknown reaction {reaction.emoji}")


client.run(token)
