import aiohttp
import discord
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
from extract import extract_rankings_from_bytes

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_message(message):
    # Ignore messages from bots
    if message.author.bot:
        return

    if message.content.strip() == "!reset":
        if message.guild is None:
            await message.reply("Reset command only works in a guild.")
            return
        channel_key = (message.guild.id, message.channel.id)
        guild_race_tables[channel_key] = pd.DataFrame(columns=["Name", "Total"])
        guild_race_tables[channel_key].index = guild_race_tables[channel_key].index + 1
        guild_all_races[channel_key] = {}
        logging.info(f"Race table reset for channel: {message.guild.name} #{message.channel.name}")
        await message.reply("Race table has been reset for this channel.")
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
                int_keys = sorted([k for k in rankings_all if isinstance(k, int)])
                str_keys = [k for k in rankings_all if isinstance(k, str)]
                sorted_ranks = int_keys + str_keys
                result = "\n".join(f"{rank} {rankings_all[rank]}" for rank in sorted_ranks)
                await message.reply(f"Ranking:\n{result}")
            else:
                # await message.reply("No rankings detected.")
                pass
with open("token.txt", "r") as f:
    token = f.read().strip()


# Mapping for digit emoji
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

guild_race_tables = {}
guild_all_races = {}
# Stores {channel_key: {original_message_id: (bot_reply_id, race_number)}}
guild_reply_maps = {}

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
        if line.startswith("Ranking:"):
            continue
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) < 2:
            continue
        try:
            if parts[0] in ('DSQ', 'DNF'):
                pos = parts[0]
            else:
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
    DSQ and DNF are equal ti the number of actual finishers in a race + 1.
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
            dsq = len([v for v in race.values() if isinstance(v, int)]) + 1
            result = race.get(participant, dns)
            if isinstance(result, int):
                total += result
            elif isinstance(result, str) and result in ('DSQ', 'DNF'):
                total += dsq
        totals[participant] = total
    return totals

def build_race_table(all_races: dict) -> pd.DataFrame:
    """
    Build a race table DataFrame from all_races and calculated totals.
    The DataFrame has the first column "Name" (ordered by total score ascending),
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
        row = {"Name": p}
        for race in race_columns:
            # Use the rank from the race if present, otherwise "DNS"
            row[str(race)] = all_races[race].get(p, "DNS")
        row["Total"] = totals[p]
        rows.append(row)
    return pd.DataFrame(rows)


def render_table_image(df: pd.DataFrame) -> BytesIO:
    """
    Render a pandas DataFrame as a PNG image with minimized whitespace.
    """
    # Set font family to support Chinese and Japanese characters
    plt.rcParams['font.family'] = 'Noto Sans CJK JP'
    df_copy = df.copy()
    # Insert numbering column at the beginning.
    df_copy.insert(0, "Rank", range(1, len(df_copy) + 1))

    new_columns = []
    for col in df_copy.columns:
        if col.isdigit():
            new_columns.append(f"Race {col}")
        else:
            new_columns.append(col)
    df_copy.columns = new_columns

    # Increase row height by ~10%
    fig, ax = plt.subplots(figsize=(len(df_copy.columns) * 2, len(df_copy) * 0.8 * 1.1))
    ax.axis('tight')
    ax.axis('off')

    tbl = ax.table(cellText=df_copy.values, colLabels=df_copy.columns, loc='center', cellLoc='center')
    tbl.auto_set_font_size(False)
    tbl.auto_set_column_width(col=list(range(len(df_copy.columns))))
    tbl.set_fontsize(10)

    # Left-align the first two columns, center-align the rest.
    for i in range(1, len(df_copy) + 1):
        tbl[(i, 0)].set_text_props(ha='center')  # First column: numbering
        if len(df_copy.columns) > 1:
            tbl[(i, 1)].set_text_props(ha='left')  # Second column: "Name"
    last_col = len(df_copy.columns) - 1
    for i in range(len(df_copy) + 1):
        tbl[(i, last_col)].get_text().set_weight('bold')

    # Apply background color to odd rows (1-indexed)
    for i in range(1, len(df_copy) + 1):
        if i % 2 == 1:
            for j in range(len(df_copy.columns)):
                tbl[(i, j)].set_facecolor("#CCFF99")
    for cell in tbl.get_celld().values():
        cell.set_linewidth(0)

    # Ensure the table is drawn so we can compute its bounding box
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bbox = tbl.get_window_extent(renderer).transformed(fig.dpi_scale_trans.inverted())

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches=bbox, pad_inches=0)
    buf.seek(0)
    plt.close(fig)
    return buf


@client.event
async def on_reaction_add(reaction, user):
    race_number = emoji_to_int.get(reaction.emoji)
    if race_number is None:
        logging.info(f"unknown reaction {reaction.emoji}")
        return

    if "Ranking:" in reaction.message.content:
        if reaction.message.guild is None:
            return
        channel_key = (reaction.message.guild.id, reaction.message.channel.id)
        new_race = parse_ranking(reaction.message.content)
        if new_race:
            if channel_key not in guild_all_races:
                guild_all_races[channel_key] = {}
            # Store the current race using the emoji value as the key
            guild_all_races[channel_key][race_number] = new_race

            # Build the race table from all stored races for this channel.
            race_table = build_race_table(guild_all_races[channel_key])
            guild_race_tables[channel_key] = race_table

            logging.info(f"Updated race table for channel: {reaction.message.guild.name} #{reaction.message.channel.name} ({channel_key})")
            logging.info(f"Race table:\n{race_table}")
            buf = render_table_image(race_table)
            # Send the reply and store the message IDs for potential future edits
            sent_message = await reaction.message.reply(file=discord.File(buf, filename="race_table.png"))
            guild_reply_maps.setdefault(channel_key, {})[reaction.message.id] = (sent_message.id, race_number)
            logging.info(f"Stored reply map for message {reaction.message.id} -> {sent_message.id} (Race {race_number})")
        else:
            logging.info("No rankings detected in message.")
    else:
        logging.info("Message does not contain rankings.")


@client.event
async def on_message_edit(before, after):
    # Ignore edits from bots or DMs
    if after.author.bot or after.guild is None:
        return

    channel_key = (after.guild.id, after.channel.id)

    # Check if this message is one we've replied to with a race table
    if channel_key in guild_reply_maps and after.id in guild_reply_maps[channel_key]:
        bot_reply_id, race_number = guild_reply_maps[channel_key][after.id]
        logging.info(f"Edited message {after.id} corresponds to race {race_number} and bot reply {bot_reply_id}")

        # Re-parse the rankings from the edited message
        new_race = parse_ranking(after.content)

        # Update the race data
        if channel_key in guild_all_races and race_number in guild_all_races[channel_key]:
            guild_all_races[channel_key][race_number] = new_race
            logging.info(f"Updated race data for race {race_number} in channel {channel_key} due to message edit.")

            # Rebuild the race table
            race_table = build_race_table(guild_all_races[channel_key])
            guild_race_tables[channel_key] = race_table # Update the stored table as well
            logging.info(f"Rebuilt race table after edit:\n{race_table}")

            # Render the new table image
            buf = render_table_image(race_table)
            new_file = discord.File(buf, filename="race_table.png")

            # Try to find and edit the original bot reply
            try:
                bot_message = await after.channel.fetch_message(bot_reply_id)
                await bot_message.edit(content=None, attachments=[new_file]) # Use attachments for files in edit
                logging.info(f"Successfully edited bot message {bot_reply_id} with updated table.")
            except discord.NotFound:
                logging.warning(f"Could not find original bot message {bot_reply_id} to edit. It might have been deleted.")
                # Optionally, post a new reply as a fallback
                # await after.reply(file=new_file)
            except discord.Forbidden:
                logging.error(f"Bot lacks permissions to edit message {bot_reply_id}.")
            except Exception as e:
                logging.error(f"Failed to edit bot message {bot_reply_id}: {e}")
        else:
            logging.warning(f"Race data for race {race_number} not found for channel {channel_key} during edit handling.")


if __name__ == '__main__':
    client.run(token)
