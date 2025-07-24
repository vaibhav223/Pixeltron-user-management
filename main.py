from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import factory
from core.config import Config
from domain.near_by_domain import init_groups
from helper.redis_helper import get_redis_conn, ensure_group

app = factory.create_app()

methods = "GET,POST,PUT,DELETE"
origins = "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=methods,
    allow_headers=["*"],
)

# @app.on_event("startup")
# async def startup():
#     await redisHelper.redisStartup()
#
#
# # Close the Redis connection when the app shuts down
# @app.on_event("shutdown")
# async def shutdown():
#     await redisHelper.redisShutdown()
@app.on_event("startup")
async def startup_event():
    redis = await get_redis_conn()

    await ensure_group(redis, Config.USER_CHAT_STREAM, Config.GROUP_NAME)
    await ensure_group(redis, Config.USER_DELIVERY_STREAM, Config.GROUP_NAME)
    print("✅ Startup tasks complete.")

if __name__ == "__main__":
    uvicorn.run("main:app",
                port=8000,
                log_level="info",
                proxy_headers=True,
                forwarded_allow_ips='*')
