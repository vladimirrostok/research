import asyncio
import os
import pandas as pd

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import PeerChannel, MessageFwdHeader

# For "fwd_from" details
from telethon.tl.types import MessageFwdHeader, PeerChannel, PeerUser, PeerChat

# Telegram credentials
api_id = ""
api_hash = ""
phone_number = ""  # Your Telegram phone number

client = TelegramClient("anon", api_id, api_hash)

# -------------------------------------------------------------------
#  HELPER: Fetch the original forwarded Message object (if accessible)
# -------------------------------------------------------------------
async def get_forwarded_original_message(fwd_from: MessageFwdHeader):
    """
    Safely fetches the original forwarded message (if any),
    and only if channel_id / channel_post exist.
    """
    if not fwd_from:
        return None

    # Safely get these attributes
    ch_id = getattr(fwd_from, "channel_id", None)
    post_id = getattr(fwd_from, "channel_post", None)

    if ch_id and post_id:
        try:
            peer = PeerChannel(ch_id)
            original_msg = await client.get_messages(peer, ids=post_id)
            return original_msg
        except Exception as e:
            print(f"[!] Could not fetch original forwarded message: {e}")
            return None

    # If there's no channel_id/post_id, likely not a channel forward
    return None

# ----------------------------------------------------------------------
#  HELPER: Build a dictionary (row) representing one message.
#          This is where we fetch + attach the original forwarded message
# ----------------------------------------------------------------------
async def build_row_for_message(msg):
    row = {
        "id": msg.id,
        "peer_id": msg.peer_id,
        "date": msg.date,
        "message": msg.message,
        "mentioned": msg.mentioned,
        "silent": msg.silent,
        "post": msg.post,
        "from_scheduled": msg.from_scheduled,
        "legacy": msg.legacy,
        "edit_hide": msg.edit_hide,
        "pinned": msg.pinned,
        "noforwards": msg.noforwards,
        "offline": msg.offline,
        "video_processing_pending": msg.video_processing_pending,
        "from_id": msg.from_id,
        "from_boosts_applied": msg.from_boosts_applied,
        "via_bot_id": msg.via_bot_id,
        "via_business_bot_id": msg.via_business_bot_id,
        "reply_to": msg.reply_to,
        "media": msg.media,
        "reply_markup": msg.reply_markup,
        "entities": msg.entities,
        "views": msg.views,
        "forwards": msg.forwards,
        "replies": msg.replies,
        "edit_date": msg.edit_date,
        "post_author": msg.post_author,
        "grouped_id": msg.grouped_id,
        "reactions": msg.reactions,
        "restriction_reason": msg.restriction_reason,
        "ttl_period": msg.ttl_period,
        "quick_reply_shortcut_id": msg.quick_reply_shortcut_id,
        "effect": msg.effect,
        "factcheck": msg.factcheck,
    }

    row["is_forwarded"]=""
    if msg.fwd_from:
        row["is_forwarded"] = True

    row["raw_msg"]=msg # raw message obj
    row["raw_fwd_from"]=msg.fwd_from  # raw string of fwd_from

    return row


# --------------------------------
#  JOIN CHANNEL
# --------------------------------
async def join_channel(channel):
    try:
        await client(JoinChannelRequest(channel))
        print(f"Successfully joined {channel}")
    except Exception as e:
        print(f"Failed to join {channel}: {e}")

# --------------------------------
#  GET ENTITY
# --------------------------------
async def get_entity(entity_name):
    try:
        entity = await client.get_entity(entity_name)
        print(f"Accessing {entity_name}")
        return entity
    except Exception as e:
        print(f"Failed to access {entity_name}: {e}")
        return None

# --------------------------------
#  SAVE TO CSV
# --------------------------------
def save_to_csv(channel, data_rows):
    if not data_rows:
        return

    os.makedirs("./data", exist_ok=True)
    channel_name = channel.replace('https://t.me/', '').replace('t.me/', '')
    file_name = f"./data/{channel_name}_messages.csv"

    df = pd.DataFrame(data_rows)
    file_exists = os.path.exists(file_name)
    df.to_csv(file_name, mode="a", header=not file_exists, index=False)
    print(f"Saved {len(data_rows)} messages to {file_name}")

# --------------------------------
#  SCRAPE MESSAGES
# --------------------------------
async def scrape_all_messages(channel, batch_size=200):
    entity = await get_entity(channel)
    if not entity:
        print(f"Failed to retrieve entity for {channel}. Skipping...")
        return

    last_message_id = None

    while True:
        try:
            raw_messages = []
            async for message in client.iter_messages(
                entity,
                limit=batch_size,
                max_id=last_message_id or 0
            ):
                raw_messages.append(message)

            if not raw_messages:
                print(f"No more messages to scrape for {channel}.")
                break

            data_rows = []
            for m in raw_messages:
                row = await build_row_for_message(m)
                data_rows.append(row)

            last_message_id = raw_messages[-1].id

            # Save partial data on the fly
            save_to_csv(channel, data_rows)

            await asyncio.sleep(1)  # short pause to avoid rate limits

        except FloodWaitError as e:
            print(f"Rate limit hit for {channel}, sleeping for {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"Error scraping {channel}: {e}")
            break

# --------------------------------
#  MAIN
# --------------------------------
async def main():
    channels = [
       # "https://t.me/disclosetv", # DiscloseTV - got banned
       # "https://t.me/rtnews", # RT News - Can't join this channel from Estonia
       # "https://t.me/washingtonpost", # The Washington Post
       # "https://t.me/politico", # Politico
       # "https://t.me/politicoeurope", # Politico Europe
       # "https://t.me/tuckercarlsonnetwork", # - Tucker Carlson Network
       # "https://t.me/Govsg", # - gov.sg
       # "https://t.me/TheBabylonBee", # - The Babylon Bee
       # "https://t.me/intelslava", # - Intel Slava Z
       # "https://t.me/Project_Veritas", # - Project Veritas
       # "https://t.me/nytimes", # - The New York Times
       # "https://t.me/bricsnews", # - BRICS News
       # "https://t.me/insiderpaper", # - Insider Paper
       # "https://t.me/WeTheMedia", # - We The Media
       # "https://t.me/hnaftali", # - Hananya Naftali - Israel News
       # "https://t.me/gatewaypunditofficial", # - Gateway Pundit
       # "https://t.me/OANNTV", # - One America News Network
       # "https://t.me/georgenews", # - GEORGENEWS
       # "https://t.me/SGTnewsNetwork", # - Sergeant News Network 🇺🇸
       # "https://t.me/WarMonitors", # - War Monitor
       # "https://t.me/Breaking911", # - Breaking911 
       # "https://t.me/TommyRobinsonNews", # - Tommy Robinson News
       # "https://t.me/police_frequency", # - Police frequency 
       # "https://t.me/vertigo_world_news", # - Vertigo World News
       # "https://t.me/WesternJournal", # - The Western Journal
       # "https://t.me/NewsmaxTV", # - Newsmax Clips
       # "https://t.me/epochtimes", # - The Epoch Times
       # "https://t.me/infodefENGLAND", # - InfoDefenseENGLISH
       # "https://t.me/Daily_Caller", # - Daily Caller  
       # "https://t.me/realDailyWire", # - Daily Wire Junkies
       # "https://t.me/WorldNews", # - World News [Breaking News]
       # "https://t.me/NTDNews", # - NTD
       # "https://t.me/trtworld", # - TRT World
       # "https://t.me/europeandusanews", # - Global News (EU, USA)
       # "https://t.me/kunuzen", # - Kun.uz English
       # "https://t.me/notboring_riga", # - not boring → Riga
       # "https://t.me/theIJR", # - Independent Journal Review
       # "https://t.me/insidekonstantinsrussia", # - INSIDE RUSSIA
       # "https://t.me/infoDefenseEn", # - IDpublicENG
       # "https://t.me/uinhurricane", # - U In Hurricane [EN]
       # "https://t.me/Ptpatriots", # - Prime Time Patriots
       # "https://t.me/benjaminnorton", # - Ben Norton - independent news
       # "https://t.me/JimmyHillReports", # - Jimmy Hill Reports △
       # "https://t.me/cbondsglobal", # - Cbonds Global 
       # "https://t.me/givebackourfreedom", # - John F. Kennedy
       # "https://t.me/MidnightRiderChannel", # - Midnight Rider Channel 🇺🇲             
       # "https://t.me/megatron_ron", # - megatron_ron
       # "https://t.me/QNewsOfficialTV",
       # "https://t.me/perplexity",
       # "https://t.me/aipost",
       # "https://t.me/hiaimediaen",
       # "https://t.me/Futurism_Science_Technology_News",
       # "https://telegram.me/cyber_security_channel",
       # "https://t.me/cybersecurityexperts",
       # "https://t.me/cloudandcybersecurity",
       # "https://telegram.me/cibsecurity",
       # "https://t.me/androidMalware",
       # "https://t.me/MalwareResearch",
       # "https://t.me/BugCrowd",
       # "https://telegram.me/itsecalert",
       # "https://t.me/reverseengineeringz",
       #"https://t.me/techleakszone",
       #"https://t.me/TechnologyBoxs",
       #"https://t.me/bsindiaofficial",
       #"https://t.me/THnewsupdates",
       #"https://t.me/bloomberg",
       "https://t.me/BizTimes"
       "https://t.me/startups",
    ]

    await client.start(phone_number)

    for channel_link in channels:
        print(f"Processing channel: {channel_link}")
        await join_channel(channel_link)
        await scrape_all_messages(channel_link)
        print(f"Finished scraping channel: {channel_link}\n")

# --------------------------------
#  Run the script
# --------------------------------
with client:
    client.loop.run_until_complete(main())