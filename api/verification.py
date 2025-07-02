from fastapi import HTTPException, APIRouter
from domain import otp_service
from domain.otp_service import update_db
from helper.response import ResponseBuilder
from schemas import otp as schemas

otp_router = APIRouter()

@otp_router.post("/send-otp", response_model=schemas.SendOtpResponse,tags=["Verification Services"])
async def send_otp(request: schemas.SendOtpRequest):
    contact = request.email if request.method == 'email' else request.mobile
    await otp_service.send_otp(contact,request.method)
    message = f"OTP sent to {request.method}: {contact}"
    return ResponseBuilder.success(message=message, code=200)


@otp_router.post("/verify-otp",tags=["Verification Services"])
async def verify_otp(request: schemas.VerifyOtpRequest):
    contact = request.email if request.method == 'email' else request.mobile
    is_verified = await otp_service.verify_otp(request.method,contact, request.otp)

    if is_verified:
        await update_db(request.method, contact)
        return ResponseBuilder.success(message="OTP Verified Successfully", code=200)
    else:
        return ResponseBuilder.error(message="Invalid or expired OTP", code=400)
