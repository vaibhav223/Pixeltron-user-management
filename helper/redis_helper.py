import redis.asyncio as redis
from core.config import Config



async def get_redis_conn():
    redis_client = redis.Redis.from_url(Config.REDIS_URL, decode_responses=True)
    return redis_client


