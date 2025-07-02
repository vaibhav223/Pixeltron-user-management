from datetime import datetime, timezone, timedelta

import jwt
from fastapi import HTTPException, Request
from passlib.context import CryptContext

from core.config import Config
from domain.session import get_mongo_client, get_collection
token_secret_key = Config.SECRET_KEY
token_algorithm = Config.ALGORITHM
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_user(data: dict) -> dict:
    """Insert a new user into the database."""
    db_client = get_mongo_client()
    users_collection = get_collection(db_client, "users")
    result = await users_collection.insert_one(data)
    return {**data, "id": str(result.inserted_id)}

async def get_user_by_email(email: str) -> dict | None:
    """Retrieve a user by their email."""
    db_client = get_mongo_client()
    users_collection = get_collection(db_client, "users")
    return await users_collection.find_one({"email": email})

# async def get_user_by_id(user_id: str) -> dict | None:
#     """Retrieve a user by their ID."""
#     return await users_collection.find_one({"_id": ObjectId(user_id)})

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    """
    Generate an access token with a short expiration time.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=int(Config.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)

async def get_user(username: str):
    db_client = await get_mongo_client()
    users_collection = await get_collection(db_client, "users")
    return await users_collection.find_one({"username": username})

def create_refresh_token(data: dict) -> str:
    """
    Generate a refresh token with a long expiration time.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=int(Config.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)


async def decode_token(token: str):
    """
    Decode and validate a JWT token.
    """
    return jwt.decode(token, token_secret_key, token_algorithm)


async def authenticate_user(username: str, password: str):

    user = await get_user(username)
    if not user:
        return None  # User not found

    if not verify_password(password, user["hashed_password"]):
        return None  # Invalid password

    return user

async def require_role(role: str,request: Request):
    """
    Ensure the user has the specified role.
    Assumes `roles` in the user model is a single string (not a list).
    """
    user = request.state.user
    print("user",user)
    user_role = user.get("role")  # Fetch the role as a string
    if not user_role:
        raise HTTPException(status_code=403, detail="User role not found")

    # Check if the user role matches the required role
    db_client = get_mongo_client()
    roles_collection = get_collection(db_client, "roles")
    role_doc = await roles_collection.find_one({"name": user_role})
    if not role_doc or role_doc["name"] != role:
        raise HTTPException(status_code=403, detail="Insufficient role")


async def require_permission(permission: str,user: dict):
    """
    Ensure the user has the specified permission.
    Assumes `roles` in the user model is a single string (not a list).
    """
    # user = request.state.user
    user_role = user.get("role")  # Fetch the role as a string
    if not user_role:
        raise HTTPException(status_code=403, detail="User role not found")

    # Find the role and fetch associated permissions
    db_client = get_mongo_client()
    roles_collection = get_collection(db_client,"roles")
    role_doc = await roles_collection.find_one({"name": user_role})
    print("role_doc",role_doc)
    if not role_doc:
        raise HTTPException(status_code=403, detail="Invalid role")

    permissions = role_doc.get("permissions", [])

    if permission not in permissions:
        raise HTTPException(status_code=403, detail="Insufficient permission")
    return permissions

# def permission_dependency(permission: str):
#     async def dependency(request: Request):
#         user = request.state.user
#         await require_permission(permission, user)
#     return Depends(dependency)

def permission_dependency(permission: str):
    async def dependency(request: Request):
        # Access user from the request state (set in middleware
        user = request.state.user
        permissions = await require_permission(permission,user)
        return permissions # Validate permission
    return dependency

