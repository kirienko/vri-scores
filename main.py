import aiohttp
import discord
import pandas as pd

from extract import extract_rankings_from_bytes
from collections import defaultdict

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_message(message):
    # Ignore messages from bots
    if message.author.bot:
        return

    if message.content.strip() == "!reset":
        global race_table
        race_table = pd.DataFrame(columns=["Participant", "Total"])
        race_table.index = race_table.index + 1
        await message.reply("Race table has been reset.")
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

all_races = {}

def parse_ranking(message_content: str) -> dict:
    """
    Parse a ranking message and return a dict mapping participants to their positions.
    Expected ranking message format (ignoring the header):
      1 SomePlayer
      2 AnotherPlayer
      3 Cool Guy
      ...
    """
    lines = message_content.splitlines()
    ranking = {}
    for line in lines:
        if line.startswith("**Ranking:**"):
            continue
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) < 2:
            continue
        try:
            pos = int(parts[0])
            participant = parts[1].strip()
            ranking[participant] = pos
        except ValueError:
            continue
    return ranking

def calculate_total(all_races: dict) -> dict:
    """
    Calculate total scores for each participant.
    For each race stored in all_races, if a participant did not start (DNS),
    substitute DNS with (number of participants across all races + 1) and sum across races.
    """
    # Determine the full set of participants across all races
    all_participants = set()
    for race in all_races.values():
        all_participants.update(race.keys())
    dns = len(all_participants) + 1
    totals = {}
    for participant in all_participants:
        total = 0
        for race in all_races.values():
            total += race.get(participant, dns)
        totals[participant] = total
    return totals

def build_race_table(all_races: dict) -> pd.DataFrame:
    """
    Build a race table DataFrame from all_races and calculated totals.
    The DataFrame has the first column "Participant" (ordered by total score ascending),
    followed by race columns (sorted numerically), and the last column "Total".
    If a participant did not take part in a race, the cell contains "DNS".
    """
    totals = calculate_total(all_races)
    # Order participants by ascending total score
    participants = sorted(totals.keys(), key=lambda p: totals[p])
    # Sort race columns numerically
    race_columns = sorted(all_races.keys())
    rows = []
    for p in participants:
        row = {"Participant": p}
        for race in race_columns:
            # Use the rank from the race if present, otherwise "DNS"
            row[str(race)] = all_races[race].get(p, "DNS")
        row["Total"] = totals[p]
        rows.append(row)
    return pd.DataFrame(rows)

@client.event
async def on_reaction_add(reaction, user):
    race_number = emoji_to_int.get(reaction.emoji)
    if race_number is None:
        print(f"unknown reaction {reaction.emoji}")
        return

    if "**Ranking:**" in reaction.message.content:
        new_race = parse_ranking(reaction.message.content)
        if new_race:
            global all_races, race_table
            # Store the current race using the emoji value as the key
            all_races[race_number] = new_race

            # Build the race table from all stored races.
            race_table = build_race_table(all_races)

            print("Updated race table:")
            print(race_table)
            table_md = race_table.to_string()
            await reaction.message.reply(f"**Overall:**\n{table_md}")
        else:
            print("No rankings detected in message.")
    else:
        print("Message does not contain rankings.")


if __name__ == '__main__':
    client.run(token)
