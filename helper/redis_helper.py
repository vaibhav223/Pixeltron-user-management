import redis.asyncio as redis
from core.config import Config



async def get_redis_conn():
    redis_client = redis.Redis.from_url(Config.REDIS_URL, decode_responses=True)
    return redis_client


async def ensure_group(redis, stream_name, group_name):
    try:
        await redis.xgroup_create(stream_name, group_name, id="$", mkstream=True)
    except Exception as e:
        if "BUSYGROUP" not in str(e):
            raise


