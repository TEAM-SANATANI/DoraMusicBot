import os
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
from motor.motor_asyncio import AsyncIOMotorClient
import yt_dlp
import requests
from keep_alive import keep_alive

# Environment Variables
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
STRING_SESSION = os.getenv("STRING_SESSION", "")  # Assistant userbot session string
MONGO_URL = os.getenv("MONGO_URL", "")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))  # Telegram Channel ID for logs

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Clients Initialization (Dora Music Bot)
app = Client("DoraMusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
assistant = Client("DoraAssistant", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
call_py = PyTgCalls(assistant)

# MongoDB Database Client
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client["dora_music_bot_db"]
chats_col = db["active_chats"]

def send_log(text: str):
    """Sends status and error logs to your Telegram log channel"""
    if LOG_CHANNEL_ID and BOT_TOKEN:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {"chat_id": LOG_CHANNEL_ID, "text": f"🎧 **Dora Music Bot Logger**:\n{text}", "parse_mode": "Markdown"}
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"Failed to send Telegram log: {e}")

# Helper to get audio stream URL from YouTube
def get_audio_url(query: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        return info['url'], info.get('title', 'Unknown Title')

@app.on_message(filters.command("play") & filters.group)
async def play_song(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("❌ Please provide a song name! Example: `/play Faded`")
    
    query = " ".join(message.command[1:])
    chat_id = message.chat.id
    msg = await message.reply("🔍 Dora is searching the song and joining voice chat via Assistant...")

    try:
        audio_url, title = get_audio_url(query)
        
        # Assistant joins voice chat and plays audio
        await call_py.join_call(
            chat_id,
            AudioPiped(audio_url)
        )
        
        await msg.edit(f"▶️ **Playing:** {title}\n👤 **Played by:** Assistant ID\n🤖 **Bot:** Dora Music Bot")
        send_log(f"✅ Song played in chat `{chat_id}`: *{title}*")
        
        # Save state in MongoDB
        await chats_col.update_one({"chat_id": chat_id}, {"$set": {"status": "playing", "last_song": title}}, upsert=True)

    except Exception as e:
        err_msg = str(e)
        logger.error(err_msg)
        send_log(f"❌ Error in chat `{chat_id}`:\n`{err_msg}`")
        await msg.edit(f"❌ Error playing song: {err_msg}")

@app.on_message(filters.command("stop") & filters.group)
async def stop_song(client: Client, message: Message):
    chat_id = message.chat.id
    try:
        await call_py.leave_call(chat_id)
        await message.reply("⏹️ Dora stopped music and left voice chat.")
        send_log(f"⏹️ Music stopped in chat `{chat_id}`")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

async def main():
    # Start web server for uptime pinging
    keep_alive()
    send_log("🚀 Dora Music Bot, Assistant, and Web Server starting up on Render...")
    
    # Start Clients
    await app.start()
    await assistant.start()
    await call_py.start()
    print("Dora Music Bot & Assistant started successfully!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
