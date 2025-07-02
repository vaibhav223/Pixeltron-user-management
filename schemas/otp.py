from pydantic import BaseModel, EmailStr, StringConstraints, model_validator
from typing import Optional, Literal, Annotated

# Define custom type for mobile using Annotated + StringConstraints
MobileStr = Annotated[str, StringConstraints(pattern=r'^\+?\d{10,15}$')]
OtpStr = Annotated[str, StringConstraints(min_length=4, max_length=6)]


class SendOtpRequest(BaseModel):
    method: Literal['email', 'mobile']
    email: Optional[EmailStr] = None
    mobile: Optional[MobileStr] = None

    @model_validator(mode='before')
    def check_contact(cls, values):
        method = values.get('method')
        email = values.get('email')
        mobile = values.get('mobile')

        if method == 'email' and not email:
            raise ValueError('Email is required for method=email')
        if method == 'mobile' and not mobile:
            raise ValueError('Mobile is required for method=mobile')
        return values


class VerifyOtpRequest(BaseModel):
    method: Literal['email', 'mobile']
    email: Optional[EmailStr] = None
    mobile: Optional[MobileStr] = None
    otp: OtpStr

    @model_validator(mode='before')
    def check_contact(cls, values):
        method = values.get('method')
        email = values.get('email')
        mobile = values.get('mobile')

        if method == 'email' and not email:
            raise ValueError('Email is required for method=email')
        if method == 'mobile' and not mobile:
            raise ValueError('Mobile is required for method=mobile')
        return values


class SendOtpResponse(BaseModel):
    message: str


class VerifyOtpResponse(BaseModel):
    verified: bool
    message: str

class VerifyLoginOtpRequest(BaseModel):
    driver_id: str
    method: Literal['email', 'mobile']
    email: Optional[EmailStr] = None
    mobile: Optional[MobileStr] = None
    otp: OtpStr

    @model_validator(mode='before')
    def check_contact(cls, values):
        method = values.get('method')
        email = values.get('email')
        mobile = values.get('mobile')

        if method == 'email' and not email:
            raise ValueError('Email is required for method=email')
        if method == 'mobile' and not mobile:
            raise ValueError('Mobile is required for method=mobile')
        return values

