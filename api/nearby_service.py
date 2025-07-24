import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from domain.near_by_domain import get_nearby_drivers_data, update_user_location
from helper.redis_helper import get_redis_conn

nearby_router = APIRouter()
DRIVER_STREAM = "driver_location_stream"
USER_STREAM = "user_location_stream"  

# @nearby_router.get("/nearby-drivers",tags=["NearBy Service"])
# async def get_nearby_drivers(
#     latitude: float = Query(..., description="Latitude of the user"),
#     longitude: float = Query(..., description="Longitude of the user"),
#     max_distance: int = Query(5000, description="Max distance in meters")):
#     resp = await get_nearby_drivers_data(longitude,latitude,max_distance)
#     return ResponseBuilder.success(data=resp, message="Data Fetched Successfully", code=200)

@nearby_router.websocket("/ws/nearby-drivers/{user_id}")
async def user_ws(websocket: WebSocket, user_id: str):
    await websocket.accept()
    group = "users"
    consumer = f"user_{user_id}"
    redis_conn = await get_redis_conn()
    task = None

    try:
        data = await websocket.receive_json()
        lat = data["lat"]
        lon = data["lon"]
        distance = data.get("distance", 0)
        await update_user_location(user_id, lat, lon)

        nearby_drivers = await get_nearby_drivers_data(lon, lat, max_distance=distance)
        if nearby_drivers:
                await websocket.send_json(nearby_drivers)
        else:
            no_drivers_payload = {
                "status": "success",
                "message": "No nearby drivers found",
                "nearbyDrivers": [],
                "totalCount": 0
            }
            await websocket.send_json(no_drivers_payload)

        async def stream_drivers():
            while True:
                try:
                    response = await redis_conn.xreadgroup(groupname=group, consumername=consumer, streams={DRIVER_STREAM: ">"}, count=10, block=0)
                    for _, messages in response:
                        for message_id, _data in messages:
                            driver_lat = float(_data["lat"])
                            driver_lon = float(_data["lon"])
                            _distance = float(_data["distance"])

                            nearby_drivers_1 = await get_nearby_drivers_data(driver_lat, driver_lon, max_distance=_distance)
                            if nearby_drivers_1:
                                    await websocket.send_json(nearby_drivers_1)
                            else:
                                no_drivers_payload1 = {
                                    "status": "success",
                                    "message": "No nearby drivers found",
                                    "nearbyDrivers": [],
                                    "totalCount": 0
                                }
                                await websocket.send_json(no_drivers_payload1)

                            await redis_conn.xack(DRIVER_STREAM, group, message_id)
                except Exception:
                    continue

        task = asyncio.create_task(stream_drivers())

        while True:
            data = await websocket.receive_json()
            lat = data["lat"]
            lon = data["lon"]
            distance = data["distance"]
            await update_user_location(user_id, lat, lon)
            await redis_conn.xadd(USER_STREAM, {"user_id": user_id, "lat": lat, "lon": lon})
            nearby_drivers = await get_nearby_drivers_data(lon, lat, max_distance=distance)
            if nearby_drivers:
                    await websocket.send_json(nearby_drivers)
            else:
                no_drivers_payload = {
                    "status": "success",
                    "message": "No nearby drivers found",
                    "nearbyDrivers": [],
                    "totalCount": 0
                }
                await websocket.send_json(no_drivers_payload)

    except WebSocketDisconnect:
        if task:
            task.cancel()
