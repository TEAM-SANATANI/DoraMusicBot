import os

API_ID = int(os.environ.get("API_ID", "1234567"))
API_HASH = os.environ.get("API_HASH", "your_api_hash_here")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token_here")

# Assistant Account ki Session String
SESSION_STRING = os.environ.get("SESSION_STRING", "your_assistant_session_string")

MONGO_DB_URI = os.environ.get("MONGO_DB_URI", "mongodb+srv://user:pass@cluster.mongodb.net/")

START_IMAGE_URL = os.environ.get(
    "START_IMAGE_URL",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1200&q=80"
)

PING_IMAGE_URL = os.environ.get(
    "PING_IMAGE_URL",
    "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?auto=format&fit=crop&w=1200&q=80"
)

BOT_NAME = "Dora Music Bot"
