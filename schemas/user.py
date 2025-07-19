from bson import ObjectId
from pydantic import BaseModel

from helper.utils import PyObjectId
# from helper.utils2 import PydanticObjectId


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token : str

class RefreshToken(BaseModel):
    refresh_token: str

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class Address(BaseModel):
    label: str                  # e.g., "Home", "Work"
    location: str               # e.g., "Bangalore"
    latitude: float
    longitude: float


class UserProfile(BaseModel):      # MongoDB ObjectId as string
    first_name: str
    middle_name:Optional[str] = None
    last_name: str
    email: EmailStr
    mobile_number: str

    is_email_verified: bool = False
    is_mobile_verified: bool = False
    profile_image: Optional[str] = None

    addresses: List[Address] = []           # Saved addresses

    is_active: bool = True
    is_blocked: bool = False

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class UserResponse(BaseModel):
    user_id: str # Accept _id from Mongo
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    email: EmailStr
    mobile_number: str

    model_config = {
        "from_attributes": True,
        "populate_by_name": False,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str
        }
    }

class CreateUserResponse(BaseModel):
    user_id: PyObjectId = Field(alias="_id")
    first_name: str
    middle_name:Optional[str] = None
    last_name: str
    email: EmailStr
    mobile_number: str

    class Config:
        populate_by_name = True  # Allows populating by _id from MongoDB
        json_encoders = {ObjectId: str}  # Converts ObjectId to str for JSON output
        arbitrary_types_allowed = True  # Allows Pydantic to handle ObjectId type


class LoginOtpRequest(BaseModel):
    contact: str
    method: str



