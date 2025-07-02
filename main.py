from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import factory
from domain.near_by_domain import init_groups

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
    await init_groups()

if __name__ == "__main__":
    uvicorn.run("main:app",
                port=8000,
                log_level="info",
                proxy_headers=True,
                forwarded_allow_ips='*')
