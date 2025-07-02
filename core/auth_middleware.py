import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import Config
from domain.user import decode_token


class TokenVerificationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, white_list_api: list[str] = None):
        super().__init__(app)
        self.white_list_api = white_list_api or (Config.WHITELIST_API.split(",") if Config.WHITELIST_API else [])

    async def dispatch(self, request: Request, call_next):
        """
        Process incoming requests to verify JWT tokens.
        """
        # Skip token verification for whitelisted routes
        if request.url.path in self.white_list_api:
            return await call_next(request)

        # Verify token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"message": "Authorization header missing or invalid"})

        token_parts = auth_header.split(" ")
        if len(token_parts) != 2 or token_parts[0] != "Bearer":
            return JSONResponse(status_code=401, content={"message": "Invalid token format"})

        token = token_parts[1]  # Extract the token part after "Bearer "

        try:
            payload = await decode_token(token)
            # payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
            request.state.user = payload  # Store decoded payload in request.state
        except jwt.ExpiredSignatureError:
            return JSONResponse(status_code=401, content={"message": "Token has expired"})
        except jwt.InvalidSignatureError:
            return JSONResponse(status_code=401, content={"message": "Invalid token signature"})
        except jwt.InvalidTokenError:
            return JSONResponse(status_code=401, content={"message": "Invalid token"})
        except Exception as e:
            return JSONResponse(status_code=500, content={"message": f"Unexpected error: {str(e)}"})
        return await call_next(request)

    # async def has_permission(self, user_roles, required_permissions):
    #     """
    #     Check if the user has the required permissions based on roles.
    #     """
    #     roles = await roles_collection.find({"_id": {"$in": user_roles}}).to_list(length=None)
    #     user_permissions = set()
    #     for role in roles:
    #         user_permissions.update(role.get("permissions", []))
    #
    #     # Check if required permissions are a subset of user permissions
    #     return set(required_permissions).issubset(user_permissions)

    # def get_required_permission(self, path: str):
    #     """
    #     Map API endpoints to required permissions.
    #     """
    #     # Define permission mapping for specific paths
    #     permission_map = {
    #         "/admin": ["admin_access"],
    #         "/edit-data": ["edit_data"],
    #         "/view-data": ["view_data"],
    #     }
    #     return permission_map.get(path, None)
