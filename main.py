import aiohttp
import discord
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
from extract import extract_rankings_from_bytes
from rapidfuzz.distance import Levenshtein # Import Levenshtein distance function

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
        # Reset data structures
        guild_race_tables[channel_key] = pd.DataFrame(columns=["Name", "Total"])
        guild_race_tables[channel_key].index = guild_race_tables[channel_key].index + 1
        guild_all_races[channel_key] = {}
        # Also clear the reference to the last message ID for this channel,
        # so the *next* table generated doesn't delete the one left behind by reset.
        if channel_key in guild_latest_table_message_id:
            del guild_latest_table_message_id[channel_key]
            logging.info(f"Cleared last table message reference for channel {channel_key} after reset.")

        logging.info(f"Race table reset for channel: {message.guild.name} #{message.channel.name}")
        await message.reply("Race table has been reset for this channel. The previous table message will remain.")
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
                rankings_all.update(ranking)

            if rankings_all:
                # --- Start: Fill gaps with "???" ---
                int_ranks = {k: v for k, v in rankings_all.items() if isinstance(k, int)}
                str_ranks = {k: v for k, v in rankings_all.items() if isinstance(k, str)}

                result_lines = []
                if int_ranks:
                    max_rank = max(int_ranks.keys())
                    # Ensure all ranks from 1 to max_rank are present
                    for i in range(1, max_rank + 1):
                        username = int_ranks.get(i, "???") # Use "???" if rank is missing
                        result_lines.append(f"{i} {username}")

                # Append string ranks (DSQ, DNF) sorted alphabetically
                for rank in sorted(str_ranks.keys()):
                    result_lines.append(f"{rank} {str_ranks[rank]}")

                result = "\n".join(result_lines)
                # --- End: Fill gaps with "???" ---

                await message.reply(f"Ranking:\n{result}")
            else:
                logging.info(f"No rankings detected in attachments for message {message.id}")
                # Optionally reply if no rankings found, currently silent
                # await message.reply("No rankings detected in the image(s).")
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
# Stores {channel_key: latest_bot_table_message_id}
guild_latest_table_message_id = {}

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
        # Correctly access channel ID via reaction.message.channel.id
        channel_key = (reaction.message.guild.id, reaction.message.channel.id)
        new_race_raw = parse_ranking(reaction.message.content)

        if new_race_raw:
            # Ensure the channel data structure exists
            if channel_key not in guild_all_races:
                guild_all_races[channel_key] = {}

            # --- Fuzzy Name Matching Logic ---
            max_distance = 2 # Max Levenshtein distance to consider a match
            processed_race = {} # Store results for this race after matching

            # Get all unique names from previous races in this channel
            existing_names = set()
            for race_data in guild_all_races.get(channel_key, {}).values():
                existing_names.update(race_data.keys())

            logging.debug(f"Existing names for fuzzy matching: {existing_names}")

            for raw_name, rank in new_race_raw.items():
                final_name = raw_name # Default to the name as parsed
                best_match_distance = max_distance + 1 # Initialize distance beyond threshold

                # Find the closest existing name within the threshold
                matched_existing_name = None
                for existing_name in existing_names:
                    distance = Levenshtein.distance(raw_name, existing_name)
                    if distance <= max_distance and distance < best_match_distance:
                        best_match_distance = distance
                        matched_existing_name = existing_name
                        # Optimization: If distance is 0 (exact match), no need to check further
                        if distance == 0:
                            break

                if matched_existing_name:
                    final_name = matched_existing_name # Use the matched existing name
                    if raw_name != final_name: # Log only if a change occurred
                        logging.info(f"Fuzzy matched new name '{raw_name}' to existing '{final_name}' (distance: {best_match_distance}) for race {race_number}")

                processed_race[final_name] = rank
            # --- End Fuzzy Name Matching Logic ---

            # Store the processed race data (with potentially corrected names)
            guild_all_races[channel_key][race_number] = processed_race

            # Build the race table from all stored races (including the newly processed one)
            race_table = build_race_table(guild_all_races[channel_key])
            guild_race_tables[channel_key] = race_table

            guild_race_tables[channel_key] = race_table

            logging.info(f"Updated race table for channel: {reaction.message.guild.name} #{reaction.message.channel.name} ({channel_key})")
            logging.info(f"Race table:\n{race_table}")
            buf = render_table_image(race_table)

            # Attempt to delete the previous table message before sending a new one
            if channel_key in guild_latest_table_message_id:
                try:
                    old_message_id = guild_latest_table_message_id[channel_key]
                    # Fetch the message object using the channel from the reaction's message
                    old_message = await reaction.message.channel.fetch_message(old_message_id)
                    await old_message.delete()
                    logging.info(f"Deleted previous race table message {old_message_id} for channel {channel_key}")
                except discord.NotFound:
                    logging.warning(f"Previous race table message {old_message_id} not found for channel {channel_key}, might have been deleted already.")
                except discord.Forbidden:
                    logging.error(f"Bot lacks permissions to delete message {old_message_id} in channel {channel_key}.")
                except Exception as e:
                    logging.error(f"Failed to delete previous race table message {old_message_id}: {e}")
                # Ensure the ID is removed from tracking even if deletion failed, to prevent repeated attempts
                del guild_latest_table_message_id[channel_key]


            # Send the new table message
            sent_message = await reaction.message.reply(file=discord.File(buf, filename="race_table.png"))
            # Store the ID of the newly sent message
            guild_latest_table_message_id[channel_key] = sent_message.id
            logging.info(f"Posted new race table message {sent_message.id} for channel {channel_key}")
        else:
            logging.info("No rankings detected in message.")
    else:
        logging.info("Message does not contain rankings.")

# Removed on_message_edit handler as it's incompatible with the single-table approach.
# Users must re-react to edited messages to update the table.

if __name__ == '__main__':
    client.run(token)
