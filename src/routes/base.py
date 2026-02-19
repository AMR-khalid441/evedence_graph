from fastapi import APIRouter ,Depends
import os
from src.helpers.config import get_settings
# Create router
base_router = APIRouter(tags=["sanitycheck"])




@base_router.get("/")
async def welcome(app_settings=Depends(get_settings)):
    
    app_name=app_settings.APP_NAME
    app_version =app_settings.APP_VERSION
    return {
        "app_name": app_name,
        "app_version":app_version,
        "message": "This is the message from router"
    }
