# backend/app/websocket/__init__.py
from fastapi import APIRouter
from .realtime_chat import router as realtime_chat_router

# 创建一个主WebSocket路由器
websocket_router = APIRouter(prefix="/ws")

# 注册realtime_chat路由器
websocket_router.include_router(realtime_chat_router)
