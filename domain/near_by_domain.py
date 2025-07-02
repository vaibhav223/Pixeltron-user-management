from datetime import datetime, timezone

from fastapi.encoders import jsonable_encoder
from redis.exceptions import ResponseError

from core.config import Config
from domain.session import get_mongo_client, get_collection
from helper.redis_helper import get_redis_conn


async def get_nearby_drivers_data(longitude,latitude,max_distance):
    db_client = await get_mongo_client()
    user_locations = await get_collection(db_client, "driver_locations")
    pipeline = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": [longitude, latitude]},
                "distanceField": "distance",
                "maxDistance": max_distance,
                "spherical": True,
                "key": "location"
            }
        },
        {
            "$lookup": {
                "from": "drivers",
                "localField": "driver_id",
                "foreignField": "_id",
                "as": "driver_profile"
            }
        },
        {
            "$unwind": {
                "path": "$driver_profile",
                "preserveNullAndEmptyArrays": False
            }
        },
        {
            "$lookup": {
                "from": "vehicles",
                "let": {"vehicleId": "$vehicle_id"},
                "pipeline": [
                    {"$addFields": {"_id_str": {"$toString": "$_id"}}},
                    {"$match": {"$expr": {"$eq": ["$_id_str", "$$vehicleId"]}}}
                ],
                "as": "vehicle_info"
            }
        },
        {
            "$unwind": {
                "path": "$vehicle_info",
                "preserveNullAndEmptyArrays": False
            }
        },
        {
            "$project": {
                "_id": 0,
                "user_id": 1,
                "distance": 1,
                "location": 1,
                "driver_profile": 1,
                "vehicle_info": 1
            }
        }
    ]

    users_data = user_locations.aggregate(pipeline)
    result_list = []

    async for doc in users_data:
        print(doc)
        doc["driver_profile"]["_id"] = str(doc["driver_profile"]["_id"])
        doc["vehicle_info"]["_id"] = str(doc["vehicle_info"]["_id"])
        result_list.append(doc)

    resp = [jsonable_encoder(item) for item in result_list]
    return resp


async def update_user_location(user_id, lat, lon):
    db_client = await get_mongo_client()
    user_locations = await get_collection(db_client, "user_locations")
    user_locations.update_one(
        {"user_id": user_id},
        {"$set": {"location": {"type": "Point", "coordinates": [lon, lat]}, "last_updated": datetime.now(timezone.utc)}},
        upsert=True,
    )

async def init_groups():
    redis_conn = await get_redis_conn()
    try:
        await redis_conn.xgroup_create(name=Config.DRIVER_STREAM, groupname="users", id="0-0", mkstream=True)
    except ResponseError:
        pass
    try:
        await redis_conn.xgroup_create(name=Config.USER_STREAM, groupname="drivers", id="0-0", mkstream=True)
    except ResponseError:
        pass