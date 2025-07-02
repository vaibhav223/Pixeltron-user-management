import os

from dotenv import load_dotenv
from fastapi import FastAPI
from api.nearby_service import nearby_router
from api.verification import otp_router
from core.auth_middleware import TokenVerificationMiddleware


def create_app():
    if not os.getenv('ENVIRONMENT', None):
        dotenv_path = 'core/.env'
        load_dotenv(dotenv_path)
    app = FastAPI(title="Ride Share Users API Documentation",
                  openapi_url="/api/openapi.json",  # Custom URL for the OpenAPI schema
                  docs_url="/api/docs",
                  redoc_url="/api/re-docs")

    # app.add_middleware(TokenVerificationMiddleware)
    app.include_router(otp_router, prefix='/api/v1')
    app.include_router(nearby_router, prefix='/api/v1')
    return app
