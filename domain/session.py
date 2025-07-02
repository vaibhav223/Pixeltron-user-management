from motor.motor_asyncio import AsyncIOMotorClient
from core.config import Config

async def get_mongo_client():
    client = AsyncIOMotorClient(Config.MONGO_URI)
    return client

async def get_collection(client,collection_name):
    db = client.get_default_database()
    collection = db.get_collection(collection_name)
    return collection