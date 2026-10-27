import os

class Config:
    API_ID = int(os.environ.get("API_ID", "0"))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    STRING_SESSION = os.environ.get("STRING_SESSION", "")  # Assistant String Session
    MONGO_DB_URI = os.environ.get("MONGO_DB_URI", "")      # MongoDB Atlas Connection URI
    BOT_NAME = os.environ.get("BOT_NAME", "Dora Music Bot")
    PORT = int(os.environ.get("PORT", 8080))
