import os
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
import yt_dlp
from flask import Flask
from threading import Thread
from config import Config
from database import add_active_chat, get_total_chats

# Flask Web Server for Render Keep-Alive
web_app = Flask('')

@web_app.route('/')
def home():
    total = get_total_chats()
    return f"{Config.BOT_NAME} is Running Active! Total database chats: {total}"

def run_web():
    web_app.run(host='0.0.0.0', port=Config.PORT)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# Pyrogram Clients Setup
bot = Client(
    "DoraMusicBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

assistant = Client(
    "DoraAssistant",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    session_string=Config.STRING_SESSION
)

call_py = PyTgCalls(assistant)

queues = {}
loop_state = {}

EMOJI_MUSIC = '<tg-emoji id="5877536313623711363">🎵</tg-emoji>'
EMOJI_STAR = '<tg-emoji id="5874948844935974490">⭐️</tg-emoji>'
EMOJI_FIRE = '<tg-emoji id="5843553939672274145">⚡️</tg-emoji>'
EMOJI_CROWN = '<tg-emoji id="5807868868886009920">👑</tg-emoji>'
EMOJI_SEARCH = '<tg-emoji id="5258503720928288433">🔎</tg-emoji>'

async def play_next(chat_id):
    if chat_id in loop_state and loop_state[chat_id]:
        if chat_id in queues and len(queues[chat_id]) > 0:
            current_song = queues[chat_id][0]
            await call_py.change_stream(chat_id, AudioPiped(current_song["url"]))
            return True

    if chat_id in queues and len(queues[chat_id]) > 0:
        queues[chat_id].pop(0)

    if chat_id in queues and len(queues[chat_id]) > 0:
        next_song = queues[chat_id][0]
        await call_py.change_stream(chat_id, AudioPiped(next_song["url"]))
        return True
    else:
        try:
            await call_py.leave_group_call(chat_id)
        except Exception:
            pass
        return False

@call_py.on_stream_end()
async def stream_end_handler(client, update):
    chat_id = update.chat_id
    await play_next(chat_id)

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    add_active_chat(message.chat.id)
    text = (
        f"👋 <b>Hey {message.from_user.first_name}!</b>\n\n"
        f"Main <b>{Config.BOT_NAME}</b> {EMOJI_CROWN} hoon!\n"
        f"Main voice chats mein high-quality music stream kar sakta hoon {EMOJI_FIRE}\n\n"
        f"<b>{EMOJI_STAR} Commands List:</b>\n"
        f"• <code>/play [song name]</code> - Play song in Voice Chat {EMOJI_MUSIC}\n"
        f"• <code>/pause</code> - Pause streaming\n"
        f"• <code>/resume</code> - Resume streaming\n"
        f"• <code>/skip</code> - Skip to next song in queue\n"
        f"• <code>/queue</code> - Show queued songs list\n"
        f"• <code>/loop</code> - Enable/Disable loop\n"
        f"• <code>/stop</code> - Stop music & leave Voice Chat"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Dora Music", url=f"https://t.me/{client.me.username}?startgroup=true")]
    ])
    await message.reply_text(text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)

@bot.on_message(filters.command("play"))
async def play_cmd(client, message):
    add_active_chat(message.chat.id)
    chat_id = message.chat.id

    if len(message.command) < 2:
        await message.reply_text("❌ <b>Song ka naam likhein!</b>\nExample: <code>/play Kesariya</code>", parse_mode=enums.ParseMode.HTML)
        return

    query = " ".join(message.command[1:])
    msg = await message.reply_text(f"{EMOJI_SEARCH} <b>{Config.BOT_NAME}</b> Searching for <code>{query}</code>...", parse_mode=enums.ParseMode.HTML)

    try:
        ydl_opts = {
            'format': 'bestaudio',
            'default_search': 'ytsearch1',
            'noplaylist': True,
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]

            title = info.get('title', 'Unknown Track')
            stream_url = info.get('url', '')
            duration = info.get('duration', 0)

        song_data = {"title": title, "url": stream_url, "duration": duration}

        if chat_id not in queues:
            queues[chat_id] = []

        queues[chat_id].append(song_data)

        if len(queues[chat_id]) == 1:
            await call_py.join_group_call(chat_id, AudioPiped(stream_url))
            await msg.edit_text(f"{EMOJI_MUSIC} <b>Playing now in Voice Chat:</b>\n<code>{title}</code>", parse_mode=enums.ParseMode.HTML)
        else:
            await msg.edit_text(f"➕ <b>Added to Queue (Position #{len(queues[chat_id])}):</b>\n<code>{title}</code>", parse_mode=enums.ParseMode.HTML)

    except Exception as e:
        await msg.edit_text(f"⚠️ <b>Error:</b> <code>{str(e)}</code>", parse_mode=enums.ParseMode.HTML)

@bot.on_message(filters.command("pause"))
async def pause_cmd(client, message):
    chat_id = message.chat.id
    try:
        await call_py.pause_stream(chat_id)
        await message.reply_text("⏸️ <b>Music Stream Paused!</b>", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"⚠️ Error: <code>{str(e)}</code>", parse_mode=enums.ParseMode.HTML)

@bot.on_message(filters.command("resume"))
async def resume_cmd(client, message):
    chat_id = message.chat.id
    try:
        await call_py.resume_stream(chat_id)
        await message.reply_text("▶️ <b>Music Stream Resumed!</b>", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"⚠️ Error: <code>{str(e)}</code>", parse_mode=enums.ParseMode.HTML)

@bot.on_message(filters.command("skip"))
async def skip_cmd(client, message):
    chat_id = message.chat.id
    try:
        res = await play_next(chat_id)
        if res:
            await message.reply_text("⏭️ <b>Skipped to next track!</b>", parse_mode=enums.ParseMode.HTML)
        else:
            await message.reply_text("⏹️ <b>Queue khali ho gayi. Left Voice Chat!</b>", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"⚠️ Error: <code>{str(e)}</code>", parse_mode=enums.ParseMode.HTML)

@bot.on_message(filters.command("queue"))
async def queue_cmd(client, message):
    chat_id = message.chat.id
    if chat_id not in queues or len(queues[chat_id]) == 0:
        await message.reply_text("📭 <b>Queue is currently empty!</b>", parse_mode=enums.ParseMode.HTML)
        return

    text = "📜 <b>Current Songs Queue:</b>\n\n"
    for idx, song in enumerate(queues[chat_id]):
        if idx == 0:
            text += f"▶️ <b>Now Playing:</b> {song['title']}\n"
        else:
            text += f"{idx}. {song['title']}\n"

    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)

@bot.on_message(filters.command("loop"))
async def loop_cmd(client, message):
    chat_id = message.chat.id
    current = loop_state.get(chat_id, False)
    loop_state[chat_id] = not current
    status = "Enabled 🔂" if loop_state[chat_id] else "Disabled ➡️"
    await message.reply_text(f"🔄 <b>Song Loop Mode is now {status}</b>", parse_mode=enums.ParseMode.HTML)

@bot.on_message(filters.command("stop"))
async def stop_cmd(client, message):
    chat_id = message.chat.id
    try:
        queues[chat_id] = []
        loop_state[chat_id] = False
        await call_py.leave_group_call(chat_id)
        await message.reply_text("⏹️ <b>Stream stopped and queue cleared!</b>", parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"⚠️ Error: <code>{str(e)}</code>", parse_mode=enums.ParseMode.HTML)

if __name__ == "__main__":
    print(f"Starting {Config.BOT_NAME}...")
    keep_alive()
    bot.start()
    assistant.start()
    call_py.start()
    print("Dora Music Bot is live & ready!")
    from pyrogram import idle
    idle()
