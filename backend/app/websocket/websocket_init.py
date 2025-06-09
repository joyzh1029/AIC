# backend/app/websocket/__init__.py
from fastapi import APIRouter
from .realtime_chat import router as realtime_chat_router

websocket_router = APIRouter()
websocket_router.include_router(realtime_chat_router, tags=["realtime-chat"])