from typing import Annotated, Any
from bson import ObjectId
from pydantic import BaseModel, Field, BeforeValidator, PlainSerializer, WithJsonSchema
from pydantic_core import CoreSchema, core_schema
# Validator function for ObjectId
def validate_object_id(v: Any) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")

# Custom type for handling MongoDB's ObjectId with Pydantic v2
PydanticObjectId = Annotated[
    ObjectId,
    BeforeValidator(validate_object_id), # Validates input to ensure it's a valid ObjectId
    PlainSerializer(lambda x: str(x), return_type=str), # Serializes ObjectId to string for JSON
    # This part is for OpenAPI schema generation in FastAPI
    WithJsonSchema({"type": "string", "format": "ObjectId"}, mode="validation"),
    WithJsonSchema({"type": "string", "format": "ObjectId"}, mode="serialization"),
]