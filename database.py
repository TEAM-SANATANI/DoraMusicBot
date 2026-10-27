from pymongo import MongoClient
from config import Config

mongo_client = MongoClient(Config.MONGO_DB_URI) if Config.MONGO_DB_URI else None
db = mongo_client["DoraMusicBot"] if mongo_client else None
chats_col = db["active_chats"] if db is not None else None

def add_active_chat(chat_id):
    if chats_col is not None:
        if not chats_col.find_one({"chat_id": chat_id}):
            chats_col.insert_one({"chat_id": chat_id})

def remove_active_chat(chat_id):
    if chats_col is not None:
        chats_col.delete_one({"chat_id": chat_id})

def get_total_chats():
    if chats_col is not None:
        return chats_col.count_documents({})
    return 0
