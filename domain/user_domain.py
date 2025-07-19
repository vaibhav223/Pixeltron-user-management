import json
import traceback
from datetime import timezone, datetime

from bson import ObjectId
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from core.config import Config
from domain.session import get_mongo_client, get_collection
from helper.mongodb_helper import serialize_doc
from helper.redis_helper import get_redis_conn
from schemas.user import UserResponse, UserProfile, CreateUserResponse


async def add_user(user_dict):
    db_client = await get_mongo_client()
    users_collection = await get_collection(db_client, "users")
    existing_driver = await users_collection.find_one({
        "$or": [
            {"email": user_dict["email"]},
            {"mobile_number": user_dict["mobile_number"]}
        ]
    })
    if existing_driver:
        if existing_driver.get("email") == user_dict["email"]:
            raise HTTPException(status_code=400, detail="User Email already exists")
        if existing_driver.get("mobile_number") == user_dict["mobile_number"]:
            raise HTTPException(status_code=400, detail="User Mobile number already exists")

    result = await users_collection.insert_one(user_dict)
    created_user = await users_collection.find_one({"_id": result.inserted_id})
    print(created_user)
    user_data = CreateUserResponse(**created_user)
    # resp = await serialize_doc(created_contractor)
    # return jsonable_encoder(resp)
    # print(user_data.model_dump())
    return jsonable_encoder(user_data, by_alias=True)


async def get_user_data(user_id):
    db_client = await get_mongo_client()
    user_collection = await get_collection(db_client, "users")
    print(user_id)
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user['user_id'] = str(user['_id'])
    del user['_id']  # Remove the original _id field
    user_data = UserResponse(**user)
    return jsonable_encoder(user_data, by_alias=True)


async def add_session_data(user_id,session_id,refresh_token,access_token,device_info={}):
    try:
        db_client = await get_mongo_client()
        session_collection = await get_collection(db_client, "user_sessions")
        await session_collection.insert_one({
            "user_id": user_id,
            "session_id": session_id,
            "device_info": device_info,
            "created_at": datetime.now(timezone.utc)
        })
        redis_conn = await get_redis_conn()
        redis_key = f'AT001##{session_id}##{access_token}'
        access_token_data = {"access_token": access_token, "refresh_token": refresh_token}
        refresh_token_redis_key = f'RT001##{session_id}##{refresh_token}'
        access_token_expire = int(Config.ACCESS_TOKEN_EXPIRE_MINUTES) * 60
        refresh_token_expire = int(Config.REFRESH_TOKEN_EXPIRE_DAYS) * 86400
        await redis_conn.setex(redis_key, access_token_expire, json.dumps(access_token_data))
        await redis_conn.setex(refresh_token_redis_key, refresh_token_expire, refresh_token)
        return True
    except Exception as e:
        traceback.print_exc()

async def check_user_data_exists(payload):
    method = payload["method"]
    contact = payload["contact"]
    db_client = await get_mongo_client()
    users_collection = await get_collection(db_client, "users")
    query = None
    if method=="email":
        query = {"email":contact}
    elif method=="mobile":
        query = {"mobile_number": contact}
    user = await users_collection.find_one(query)
    if user:
        return user,True
    else:
        return {},False

async def save_token_data(session_id,old_access_token,access_token):
    redis_client = await get_redis_conn()
    redis_key = f'AT001##{session_id}##{old_access_token}'
    await redis_client.delete(redis_key)
    access_token_expire = int(Config.ACCESS_TOKEN_EXPIRE_MINUTES) * 60
    await redis_client.setex(redis_key, access_token_expire, access_token)
    return True

async def get_active_sessions(user_id):
    resp = []
    db_client = await get_mongo_client()
    session_collection = await get_collection(db_client, "user_sessions")
    sessions = await session_collection.find({"user_id": user_id}).to_list(100)
    if sessions:
        result = [await serialize_doc(item) for item in sessions]
        resp = [jsonable_encoder(item) for item in result]
    return resp


async def logout_user(session_id,access_token):
    db_client = await get_mongo_client()
    session_collection = await get_collection(db_client, "user_sessions")
    delete_result = await session_collection.delete_one({"session_id": session_id})
    redis_client = await get_redis_conn()
    redis_key = f'AT001##{session_id}##{access_token}'
    token_data = await redis_client.get(redis_key)
    stored_token = json.loads(token_data)
    refresh_token_redis_key = f'RT001##{session_id}##{stored_token["refresh_token"]}'
    await redis_client.delete(refresh_token_redis_key)
    await redis_client.delete(redis_key)
    return True