import traceback

from fastapi import Depends, HTTPException
import jwt
from pydantic import BaseModel

from core.config import Config
from domain.user import decode_token
from helper.redis_helper import get_redis_conn
from helper.response import ResponseBuilder


class TokenData(BaseModel):
    user_id: str
    session_id: str

class AuthService:
    def __init__(self, secret_key=Config.SECRET_KEY, algorithm=Config.ALGORITHM):
        self.secret_key = secret_key
        self.algorithm = algorithm

    async def get_current_user(self, token: str) -> TokenData:
        try:
            redis_client = await get_redis_conn()
            payload = await decode_token(token)
            session_id = payload["session_id"]
            user_id = payload["user_id"]
            redis_key = f'AT001##{session_id}##{token}'
            stored_token = await redis_client.get(redis_key)
            user_id = payload.get("user_id")
            session_id = payload.get("session_id")

            if not user_id or not session_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")


            return TokenData(user_id=user_id, session_id=session_id)

        except Exception:
            traceback.print_exc()
            raise HTTPException(status_code=401, detail="Invalid or expired token")
