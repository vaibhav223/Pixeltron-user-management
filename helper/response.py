from fastapi.responses import JSONResponse,Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import json


class ResponseBuilder:
    def __init__(self, status: str, code: int, message: str, data=None, errors=None):
        self.status = status
        self.code = code
        self.message = message
        self.data = data
        self.errors = errors

    def build(self):
        if self.code == 204:
            return Response(status_code=204)
        return JSONResponse(
            status_code=self.code,
            content={
                "status": self.status,
                "code": self.code,
                "message": self.message,
                "data": self.data,
                "errors": self.errors
            }
        )

    @classmethod
    def success(cls, data=None, message="Success", code=200):
        return cls("success", code, message, data=data, errors=None).build()

    @classmethod
    def error(cls, message="Error", code=500, errors=None):
        return cls("error", code, message, data=None, errors=errors or {}).build()


# class ResponseWrapperMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         try:
#             response = await call_next(request)
#
#             if response.media_type != "application/json":
#                 return response
#
#             body = [section async for section in response.body_iterator]
#             raw_body = b"".join(body).decode("utf-8")
#
#             try:
#                 data = json.loads(raw_body)
#             except json.JSONDecodeError:
#                 return response
#
#             status = "error" if response.status_code >= 400 else "success"
#             message = data.get("message", "Error" if status == "error" else "Success")
#
#             return ResponseBuilder(
#                 status=status,
#                 code=response.status_code,
#                 message=message,
#                 data=None if status == "error" else data,
#                 errors=data if status == "error" else None
#             ).build()
#
#         except Exception as e:
#             return ResponseBuilder.error(message="Internal Server Error", code=500, errors={"detail": str(e)})
#
#
# def response_wrapper(success_message="Success", error_message="Error"):
#     def decorator(func):
#         async def wrapper(*args, **kwargs):
#             try:
#                 result = await func(*args, **kwargs)
#                 return ResponseBuilder.success(data=result, message=success_message)
#             except Exception as e:
#                 return ResponseBuilder.error(message=error_message, errors={"detail": str(e)})
#         return wrapper
#     return decorator

# from utils.response import ResponseBuilder
#
# # Success response
# return ResponseBuilder.success(data={"foo": "bar"}, message="Fetched", code=200)
#
# # Error response
# return ResponseBuilder.error(message="Bad request", code=400, errors={"field": "id"})
