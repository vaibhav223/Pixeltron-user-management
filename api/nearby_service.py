import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from domain.near_by_domain import get_nearby_drivers_data, update_user_location
from helper.redis_helper import get_redis_conn

nearby_router = APIRouter()

CHAT_STREAM = "chat_stream"
USER_DELIVERY_STREAM = "user_delivery_stream"
DRIVER_DELIVERY_STREAM = "driver_delivery_stream"
DRIVER_LOCATION_STREAM = "driver_location_stream"
USER_LOCATION_STREAM = "user_location_stream"
USER_CHAT_STREAM = "user_chat_stream"
DRIVER_CHAT_STREAM = "driver_chat_stream"

# @nearby_router.get("/nearby-drivers",tags=["NearBy Service"])
# async def get_nearby_drivers(
#     latitude: float = Query(..., description="Latitude of the user"),
#     longitude: float = Query(..., description="Longitude of the user"),
#     max_distance: int = Query(5000, description="Max distance in meters")):
#     resp = await get_nearby_drivers_data(longitude,latitude,max_distance)
#     return ResponseBuilder.success(data=resp, message="Data Fetched Successfully", code=200)

@nearby_router.websocket("/ws/nearby-drivers/{user_id}")
async def user_websocket_handler(websocket: WebSocket, user_id: str):
    await websocket.accept()
    redis = await get_redis_conn()

    group = "users"
    consumer = user_id
    stop_event = asyncio.Event()


    async def claim_pending_messages():
        try:
            pending = await redis.xpending_range(USER_CHAT_STREAM, group, "-", "+", 50)
            for entry in pending:
                if entry.consumer != consumer:
                    claimed = await redis.xclaim(USER_CHAT_STREAM, group, consumer, 10000, [entry.message_id])
                    for msg_id, msg in claimed:
                        if msg.get("to") == user_id:
                            await websocket.send_json(build_chat_response(msg_id, msg))
                            await redis.xack(USER_CHAT_STREAM, group, msg_id)
                            await redis.xdel(USER_CHAT_STREAM, msg_id)
        except Exception as e:
            print(f"[user:{user_id}] claim error: {e}")

    def build_chat_response(msg_id, msg):
        if msg.get("media_url"):
            return {
                "type": "media",
                "msg_id": msg_id,
                "from": msg.get("from"),
                "media_url": msg.get("media_url"),
                "media_type": msg.get("media_type"),
                "filename": msg.get("filename", ""),
                "duration": float(msg.get("duration", 0))
            }
        return {
            "type": "chat",
            "msg_id": msg_id,
            "from": msg.get("from"),
            "message": msg.get("message")
        }

    async def redis_listener():
        await claim_pending_messages()

        while not stop_event.is_set():
            try:
                response = await redis.xreadgroup(
                    groupname=group,
                    consumername=consumer,
                    streams={USER_CHAT_STREAM: ">", USER_DELIVERY_STREAM: ">"},
                    count=10,
                    block=1000
                )
                for stream, messages in response:
                    for msg_id, msg in messages:
                        try:
                            if stream == USER_CHAT_STREAM and msg.get("to") == user_id:
                                await websocket.send_json(build_chat_response(msg_id, msg))
                                await redis.xack(USER_CHAT_STREAM, group, msg_id)
                                await redis.xdel(USER_CHAT_STREAM, msg_id)
                            elif stream == USER_DELIVERY_STREAM and msg.get("to") == user_id:
                                await websocket.send_json({
                                    "type": "delivery_receipt",
                                    "msg_id": msg.get("msg_id"),
                                    "status": msg.get("status")
                                })
                                await redis.xack(USER_DELIVERY_STREAM, group, msg_id)
                                await redis.xdel(USER_DELIVERY_STREAM, msg_id)
                        except:
                            stop_event.set()
                            return
            except Exception as e:
                print(f"[user:{user_id}] Redis error: {e}")
                await asyncio.sleep(1)

    task = asyncio.create_task(redis_listener())

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "chat":
                await redis.xadd(DRIVER_CHAT_STREAM, {
                    "from": user_id,
                    "to": data["to_driver_id"],
                    "sender_type": "user",
                    "message": data["message"]
                })

            elif msg_type == "media":
                await redis.xadd(DRIVER_CHAT_STREAM, {
                    "from": user_id,
                    "to": data["to_driver_id"],
                    "sender_type": "user",
                    "media_url": data["media_url"],
                    "media_type": data["media_type"],
                    "filename": data.get("filename", ""),
                    "duration": str(data.get("duration", ""))
                })

            elif msg_type == "location":
                lat, lon = float(data["lat"]), float(data["lon"])
                dist = int(data.get("distance", 3000))
                await update_user_location(user_id, lat, lon)
                # await redis.xadd(USER_LOCATION_STREAM, {
                #     "user_id": user_id,
                #     "lat": lat,
                #     "lon": lon
                # })
                nearby_drivers = await get_nearby_drivers_data(lon, lat, max_distance=30000)
                if nearby_drivers:
                    resp = {
                        "type": "nearby_drivers",
                        "status": "success",
                        "nearbyDrivers": nearby_drivers,
                        "totalCount": 0
                    }
                    await websocket.send_json(resp)
                else:
                    no_drivers_payload = {
                        "type": "nearby_drivers",
                        "status": "success",
                        "message": "No nearby drivers found",
                        "nearbyDrivers": [],
                        "totalCount": 0
                    }
                    await websocket.send_json(no_drivers_payload)


            elif msg_type in ("delivered", "seen"):
                await redis.xadd(DRIVER_DELIVERY_STREAM, {
                    "msg_id": data["msg_id"],
                    "from": user_id,
                    "to": data["to"],
                    "status": msg_type
                })

    except WebSocketDisconnect:
        print(f"User disconnected: {user_id}")
    finally:
        stop_event.set()
        await task
