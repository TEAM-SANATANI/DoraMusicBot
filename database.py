from motor.motor_asyncio import AsyncIOMotorClient
import config

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(config.MONGO_DB_URI)
        self.db = self.client["DoraMusicDB"]
        self.users = self.db["users"]
        self.chats = self.db["chats"]
        self.autoplay = self.db["autoplay"]

    async def add_user(self, user_id: int):
        if not await self.users.find_one({"user_id": user_id}):
            await self.users.insert_one({"user_id": user_id})

    async def add_chat(self, chat_id: int):
        if not await self.chats.find_one({"chat_id": chat_id}):
            await self.chats.insert_one({"chat_id": chat_id})

    async def set_autoplay(self, chat_id: int, state: bool):
        await self.autoplay.update_one(
            {"chat_id": chat_id},
            {"$set": {"status": state}},
            upsert=True
        )

    async def get_autoplay(self, chat_id: int) -> bool:
        data = await self.autoplay.find_one({"chat_id": chat_id})
        return data["status"] if data else False

db = Database()
