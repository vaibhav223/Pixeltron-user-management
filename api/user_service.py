import traceback
from uuid import uuid4
import jwt
from fastapi import APIRouter,Request
from domain import otp_service
from domain.user import create_access_token, create_refresh_token, decode_token
from domain.user_domain import add_user, get_user_data, add_session_data, save_token_data, \
    get_active_sessions, logout_user, check_user_data_exists
from helper.redis_helper import get_redis_conn
from helper.response import ResponseBuilder
from helper.token_data_helper import AuthService
from schemas.otp import VerifyLoginOtpRequest
from schemas.user import UserProfile, LoginOtpRequest, RefreshToken

user_router = APIRouter()

@user_router.post("/user/register",tags=["Verification Services"])
async def send_otp(data: UserProfile):
    driver_dict = data.model_dump(by_alias=True)
    resp = await add_user(driver_dict)
    return ResponseBuilder.success(data=resp,message="User Created Successfully", code=201)


@user_router.get("/user/profile",tags=["User Services"])
async def get_user(request:Request):
    access_token = request.headers.get('accesstoken')
    auth_service = AuthService()
    user = await auth_service.get_current_user(access_token)
    resp = await get_user_data(user.user_id)
    return ResponseBuilder.success(data=resp,message="Data Fetched Successfully", code=200)

@user_router.post("/user/login/otp",tags=["Driver Authentication Services"])
async def delete_driver(request:Request):
    payload = await request.json()
    LoginOtpRequest.model_validate(payload)
    user,is_exists = await check_user_data_exists(payload)
    if user and is_exists:
        contact = payload["contact"]
        await otp_service.send_otp(contact, payload["method"])
        result = dict(driver_id=str(user["_id"]))

        return ResponseBuilder.success(data=result, message="Otp Sent Successfully", code=200)
    else:
        return ResponseBuilder.success(message="User Not Exists", code=204)



@user_router.post("/user/login",tags=["Driver Authentication Services"])
async def login(request:Request,data:VerifyLoginOtpRequest):
    payload = await request.json()
    VerifyLoginOtpRequest.model_validate(payload)
    contact = data.email if data.method == 'email' else data.mobile
    payload["contact"] = contact
    user, is_exists = await check_user_data_exists(payload)
    # is_verified = await otp_service.verify_otp(data.method, contact, data.otp)
    is_verified = True
    if is_verified:
        session_id = str(uuid4())

        access_token = create_access_token({"user_id": str(user["_id"]),"session_id":session_id})
        refresh_token = create_refresh_token({"user_id": str(user["_id"]),"session_id":session_id})
        status = await add_session_data(str(user["_id"]), session_id,refresh_token,access_token)
        if status:
            resp = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "session_id":session_id,
                "user_id":str(user["_id"])
            }
            return ResponseBuilder.success(data=resp, message="Login Successful", code=200)
        else:
            return ResponseBuilder.error(message="Failure", code=400)


    else:
        return ResponseBuilder.error(message="Invalid or expired OTP", code=400)

@user_router.post("/user/refresh-token",tags=["Driver Authentication Services"])
async def get_refresh_token(data: RefreshToken,request:Request):
    """
    Generate a new access token using a valid refresh token.
    """
    try:
        access_token = request.headers.get('accesstoken')
        payload = await decode_token(data.refresh_token)
        session_id = payload["session_id"]
        user_id = payload["user_id"]
        redis_client = await get_redis_conn()
        refresh_token_redis_key = f'RT001##{session_id}##{data.refresh_token}'
        stored_token = await redis_client.get(refresh_token_redis_key)
        if stored_token != data.refresh_token:
            return ResponseBuilder.error(message="Invalid refresh token", code=401)
        elif payload.get("type") != "refresh":
            return ResponseBuilder.error(message="Invalid token type", code=400)

        new_access_token = create_access_token({"user_id": user_id,"session_id":session_id})
        result = await save_token_data(session_id,access_token,new_access_token)
        resp = {"access_token": new_access_token, "token_type": "bearer","session_id":session_id}
        return ResponseBuilder.success(data=resp, message="Data Fetched Successfully", code=200)
    except jwt.ExpiredSignatureError:
        return ResponseBuilder.error(message="Token has expired", code=401)
    except jwt.InvalidSignatureError:
        return ResponseBuilder.error(message="Invalid token signature", code=400)
    except jwt.InvalidTokenError:
        return ResponseBuilder.error(message="Invalid token", code=401)
    except Exception as e:
        traceback.print_exc()
        return ResponseBuilder.error(message="Something Went Wrong", code=500,errors=e)


@user_router.post("/user/logout")
async def logout(request:Request):
    access_token = request.headers.get('accesstoken')
    auth_service = AuthService()
    user = await auth_service.get_current_user(access_token)
    is_logged_out = await logout_user(user.session_id,access_token)
    if is_logged_out:
        return ResponseBuilder.success(message="Logout Successfully", code=200)
    else:
        return ResponseBuilder.error(message="Error In Logout", code=400)

@user_router.get("/user/active/sessions")
async def get_active_user_sessions(request:Request):
    access_token = request.headers.get('accesstoken')
    auth_service = AuthService()
    user = await auth_service.get_current_user(access_token)
    resp = await get_active_sessions(user.user_id)
    if resp:
        return ResponseBuilder.success(data=resp, message="Data Fetched Successfully", code=200)
    else:
        return ResponseBuilder.success(message="No Data Found", code=204)


