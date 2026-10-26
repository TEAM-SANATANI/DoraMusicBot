import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
from yt_dlp import YoutubeDL

import config
from database import db

# Main Bot Client
app = Client(
    "DoraMusicBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

# Assistant Account (Userbot) Client
userbot = Client(
    "DoraAssistant",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    session_string=config.SESSION_STRING
)

# Call Client bind with Assistant
call_app = PyTgCalls(userbot)

queues = {}
ytdl_opts = {"format": "bestaudio/best", "quiet": True}

def get_yt_audio(query: str):
    with YoutubeDL(ytdl_opts) as ytdl:
        info = ytdl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        return info['url'], info['title'], info['duration'], info['webpage_url']

# Helper Function: Auto Join Assistant if not in Group
async def join_assistant(chat_id: int):
    try:
        await userbot.get_chat_member(chat_id, "me")
    except Exception:
        try:
            chat = await app.get_chat(chat_id)
            if chat.username:
                await userbot.join_chat(chat.username)
            else:
                invite_link = await app.export_chat_invite_link(chat_id)
                await userbot.join_chat(invite_link)
        except Exception as e:
            raise Exception(f"Assistant group join nahi kar saka. Pehle Assistant ID ko group me add karein. Error: {e}")

@app.on_message(filters.command("play") & filters.group)
async def play_cmd(client, message: Message):
    chat_id = message.chat.id
    
    if len(message.command) < 2:
        return await message.reply("⚠️ **Usage:** `/play <song name or link>`")

    query = " ".join(message.command[1:])
    m = await message.reply("🔎 **Searching & Preparing Assistant...**")

    # Step 1: Ensure Assistant is in group
    try:
        await join_assistant(chat_id)
    except Exception as e:
        return await m.edit(f"❌ {e}")

    # Step 2: Fetch Youtube Audio Stream
    try:
        url, title, duration, link = get_yt_audio(query)
    except Exception as e:
        return await m.edit(f"❌ **Error fetching track:** {e}")

    track = {"title": title, "url": url, "link": link}

    if chat_id not in queues:
        queues[chat_id] = []

    queues[chat_id].append(track)

    # Step 3: Stream song via Assistant ID
    if len(queues[chat_id]) == 1:
        try:
            await call_app.play(chat_id, AudioPiped(url))
            await m.edit(f"🎶 **Now Playing by Assistant:** [{title}]({link})")
        except Exception as e:
            await m.edit(f"❌ Voice Chat connect nahi ho saka. Group me Voice Chat start karein.\n\nError: {e}")
    else:
        await m.edit(f"➕ **Added to Queue (#{len(queues[chat_id])}):** [{title}]({link})")

@call_app.on_stream_end()
async def stream_end_handler(client, update):
    chat_id = update.chat_id
    if chat_id in queues and queues[chat_id]:
        queues[chat_id].pop(0)

    if chat_id in queues and len(queues[chat_id]) > 0:
        next_track = queues[chat_id][0]
        await call_app.play(chat_id, AudioPiped(next_track['url']))
        await app.send_message(chat_id, f"🎶 **Auto-Playing Next:** [{next_track['title']}]({next_track['link']})")
    else:
        is_autoplay = await db.get_autoplay(chat_id)
        if is_autoplay:
            url, title, duration, link = get_yt_audio("Hindi Top Songs 2026")
            await call_app.play(chat_id, AudioPiped(url))
            await app.send_message(chat_id, f"🔁 **Autoplay Triggered:** [{title}]({link})")

async def main():
    await app.start()
    await userbot.start()
    await call_app.start()
    print("✨ Dora Music Bot & Assistant successfully connected!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
