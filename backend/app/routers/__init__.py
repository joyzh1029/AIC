"""
路由管理模块
此模块负责集中管理和注册所有API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Callable, List, Dict, Any

# 创建主路由器
api_router = APIRouter()

# 导入所有子路由器
from app.routers.avatar import router as avatar_router
from app.routers.chat import router as chat_router
from app.routers.camera import router as camera_router
from app.routers.emotion import router as emotion_router

# 注册所有路由器
api_router.include_router(avatar_router)
api_router.include_router(chat_router)
api_router.include_router(camera_router)
api_router.include_router(emotion_router)

# 导出所有路由器，方便在main.py中一次性注册
__all__ = ["api_router"]
