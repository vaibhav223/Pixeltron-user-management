import traceback

from fastapi import Depends, HTTPException
import jwt
from pydantic import BaseModel

from core.config import Config


class TokenData(BaseModel):
    user_id: str
    session_id: str

class AuthService:
    def __init__(self, secret_key=Config.SECRET_KEY, algorithm=Config.ALGORITHM):
        self.secret_key = secret_key
        self.algorithm = algorithm

    async def get_current_user(self, token: str) -> TokenData:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            session_id = payload.get("session_id")
            print(payload)
            print(session_id)

            if not user_id or not session_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")


            return TokenData(user_id=user_id, session_id=session_id)

        except Exception:
            traceback.print_exc()
            raise HTTPException(status_code=401, detail="Invalid or expired token")
