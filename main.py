import asyncio
import pandas as pd
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import JoinChannelRequest

# Telegram API credentials
api_id = ""
api_hash = ""
phone_number = ""  # Your Telegram phone number

client = TelegramClient("anon", api_id, api_hash)

async def join_channel(client, channel):
    try:
        await client(JoinChannelRequest(channel))
        print(f"Successfully joined {channel}")
    except Exception as e:
        print(f"Failed to join {channel}: {e}")

async def get_entity(entity_name):
    try:
        entity = await client.get_entity(entity_name)
        print(f"Accessing {entity_name}")
        return entity
    except Exception as e:
        print(f"Failed to access {entity_name}: {e}")
        return None

def save_to_csv(channel, messages):
    if not messages:
        return

    data = []
    for message in messages:
        data.append({
            "id": message.id,
            "peer_id": str(message.peer_id),
            "date": message.date,
            "message": message.message,
            "out": message.out,
            "mentioned": message.mentioned,
            "media_unread": message.media_unread,
            "silent": message.silent,
            "post": message.post,
            "from_scheduled": message.from_scheduled,
            "legacy": message.legacy,
            "edit_hide": message.edit_hide,
            "pinned": message.pinned,
            "noforwards": message.noforwards,
            "invert_media": message.invert_media,
            "offline": message.offline,
            "video_processing_pending": message.video_processing_pending,
            "from_id": str(message.from_id),
            "from_boosts_applied": message.from_boosts_applied,
            "saved_peer_id": str(message.saved_peer_id),
            "fwd_from": str(message.fwd_from),
            "via_bot_id": message.via_bot_id,
            "via_business_bot_id": message.via_business_bot_id,
            "reply_to": str(message.reply_to),
            "media": str(message.media),
            "reply_markup": str(message.reply_markup),
            "entities": str(message.entities),
            "views": message.views,
            "forwards": message.forwards,
            "replies": str(message.replies),
            "edit_date": message.edit_date,
            "post_author": message.post_author,
            "grouped_id": message.grouped_id,
            "reactions": str(message.reactions),
            "restriction_reason": str(message.restriction_reason),
            "ttl_period": message.ttl_period,
            "quick_reply_shortcut_id": message.quick_reply_shortcut_id,
            "effect": message.effect,
            "factcheck": message.factcheck,
        })

    df = pd.DataFrame(data)
    file_name = f"{"./data/"+channel.replace('https://t.me/', '')}_messages.csv"

    df.to_csv(file_name, mode="a", header=not pd.io.common.file_exists(file_name), index=False)
    print(f"Saved {len(messages)} messages to {file_name}")

async def scrape_all_messages(client, channel, batch_size=500):
    entity = await get_entity(channel)
    if not entity:
        print("Failed to retrieve entity. Exiting...")
        return

    last_message_id = None  # Track last message ID

    while True:
        try:
            messages = []
            async for message in client.iter_messages(entity, limit=batch_size, max_id=last_message_id or 0):
                messages.append(message)

            if not messages:
                print("No more messages to scrape.")
                break  # Exit loop if no messages are left

            last_message_id = messages[-1].id  # Update last processed message ID
            save_to_csv(channel, messages)
            await asyncio.sleep(1)  # Small delay to avoid rate limits

        except FloodWaitError as e:
            print(f"Rate limit hit, sleeping for {e.seconds} seconds")
            await asyncio.sleep(e.seconds)  # Async-friendly delay
        except Exception as e:
            print(f"Error: {e}")
            break  # Stop on unexpected errors

# https://t.me/washingtonpost # The Washington Post
# https://t.me/politico # Politico
# https://t.me/politicoeurope # Politico Europe

# List from https://tlgrm.eu/channels/news
# ______
# https://t.me/tuckercarlsonnetwork - Tucker Carlson Network
# https://t.me/disclosetv - DiscloseTV
# https://t.me/Govsg - gov.sg
# https://t.me/TheBabylonBee - The Babylon Bee
# https://t.me/intelslava - Intel Slava Z
# https://t.me/Project_Veritas - Project Veritas
# https://t.me/nytimes - The New York Times
# https://t.me/bricsnews - BRICS News
# https://t.me/insiderpaper - Insider Paper
# https://t.me/WeTheMedia - We The Media
# https://t.me/hnaftali - Hananya Naftali - Israel News
# https://t.me/gatewaypunditofficial - Gateway Pundit
# https://t.me/OANNTV - One America News Network
# https://t.me/georgenews - GEORGENEWS
# https://t.me/SGTnewsNetwork - Sergeant News Network 🇺🇸
# https://t.me/WarMonitors - War Monitor
# https://t.me/rtnews # RT News - Can't join this channel from Estonia
# https://t.me/Breaking911 - Breaking911 
# https://t.me/TommyRobinsonNews - Tommy Robinson News
# https://t.me/police_frequency - Police frequency 
# https://t.me/vertigo_world_news - Vertigo World News
# https://t.me/WesternJournal - The Western Journal
# https://t.me/NewsmaxTV - Newsmax Clips
# https://t.me/epochtimes - The Epoch Times
# https://t.me/infodefENGLAND - InfoDefenseENGLISH
# https://t.me/Daily_Caller - Daily Caller  
# https://t.me/realDailyWire - Daily Wire Junkies
# https://t.me/WorldNews - World News [Breaking News]
# https://t.me/NTDNews - NTD
# https://t.me/trtworld - TRT World
# https://t.me/europeandusanews - Global News (EU, USA)
# https://t.me/kunuzen - Kun.uz English
# X https://t.me/elsaltodiario - elsaltodiario.com 
# https://t.me/notboring_riga - not boring → Riga
# https://t.me/theIJR - Independent Journal Review
# https://t.me/insidekonstantinsrussia - INSIDE RUSSIA
# X https://t.me/belgorodskiy_kray - Белгородский Край ❤️ БК.
# https://t.me/infoDefenseEn - IDpublicENG
# https://t.me/uinhurricane - U In Hurricane [EN]
# https://t.me/Ptpatriots - Prime Time Patriots
# https://t.me/benjaminnorton - Ben Norton - independent news
# https://t.me/JimmyHillReports - Jimmy Hill Reports △
# https://t.me/cbondsglobal - Cbonds Global 
# https://t.me/givebackourfreedom - John F. Kennedy
# https://t.me/MidnightRiderChannel - Midnight Rider Channel 🇺🇲             
# https://t.me/megatron_ron - megatron_ron

async def main():
    channel_link = "https://t.me/politicoeurope"

    await client.start(phone_number)
    await join_channel(client, channel_link)
    await scrape_all_messages(client, channel_link)

with client:
    client.loop.run_until_complete(main())