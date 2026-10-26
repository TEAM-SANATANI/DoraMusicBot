import sys
import asyncio

# Python 3.10+ Event Loop Clean Fix
if sys.version_info >= (3, 10):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        except Exception:
            pass

import time
import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls import StreamAudio
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

@app.on_message(filters.command("start"))
async def start_cmd(client, message: Message):
    await db.add_user(message.from_user.id)
    if message.chat.type.value in ["group", "supergroup"]:
        await db.add_chat(message.chat.id)

    caption = (
        f"✨ **Welcome to {config.BOT_NAME}!**\n\n"
        f"🎵 High-quality music player for your Telegram Voice Chats.\n\n"
        f"• Direct YT Search & Playback via Assistant ID\n"
        f"• Auto-play Next Track\n"
        f"• Speed & Ping Diagnostics"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{client.me.username}?startgroup=true")],
        [InlineKeyboardButton("📢 Support", url="https://t.me/Telegram"), InlineKeyboardButton("⚙️ Settings", callback_data="settings_menu")]
    ])
    await message.reply_photo(photo=config.START_IMAGE_URL, caption=caption, reply_markup=buttons)

@app.on_message(filters.command("ping"))
async def ping_cmd(client, message: Message):
    start_time = time.time()
    msg = await message.reply("⏳ Checking latency...")
    end_time = time.time()
    ping_ms = round((end_time - start_time) * 1000, 2)

    caption = f"🚀 **{config.BOT_NAME} Status**\n\n⚡ **Latency:** `{ping_ms} ms`\n🤖 **Engine Status:** Online"
    await msg.delete()
    await message.reply_photo(photo=config.PING_IMAGE_URL, caption=caption)

@app.on_message(filters.command("play") & filters.group)
async def play_cmd(client, message: Message):
    chat_id = message.chat.id
    
    if len(message.command) < 2:
        return await message.reply("⚠️ **Usage:** `/play <song name or link>`")

    query = " ".join(message.command[1:])
    m = await message.reply("🔎 **Searching & Preparing Assistant...**")

    try:
        await join_assistant(chat_id)
    except Exception as e:
        return await m.edit(f"❌ {e}")

    try:
        url, title, duration, link = get_yt_audio(query)
    except Exception as e:
        return await m.edit(f"❌ **Error fetching track:** {e}")

    track = {"title": title, "url": url, "link": link}

    if chat_id not in queues:
        queues[chat_id] = []

    queues[chat_id].append(track)

    if len(queues[chat_id]) == 1:
        try:
            await call_app.join_group_call(
                chat_id,
                StreamAudio(url),
                stream_type=AudioStream
            )
            await m.edit(f"🎶 **Now Playing by Assistant:** [{title}]({link})")
        except Exception as e:
            # Fallback for alternative stream methods if call is already joined
            try:
                await call_app.change_stream(chat_id, StreamAudio(url))
                await m.edit(f"🎶 **Now Playing by Assistant:** [{title}]({link})")
            except Exception as ex:
                await m.edit(f"❌ Voice Chat connect nahi ho saka. Group me Voice Chat start karein.\n\nError: {ex}")
    else:
        await m.edit(f"➕ **Added to Queue (#{len(queues[chat_id])}):** [{title}]({link})")

@app.on_message(filters.command("autoplay") & filters.group)
async def toggle_autoplay(client, message: Message):
    chat_id = message.chat.id
    current_state = await db.get_autoplay(chat_id)
    new_state = not current_state
    await db.set_autoplay(chat_id, new_state)

    status = "Enabled 🟢" if new_state else "Disabled 🔴"
    await message.reply(f"🔁 **Autoplay status updated:** {status}")

async def main():
    await app.start()
    await userbot.start()
    await call_app.start()
    print("✨ Dora Music Bot & Assistant successfully connected!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
