"""
API 라우터 모듈
이 모듈은 모든 API 라우트를 중앙 집중식으로 관리하고 등록하는 역할을 합니다
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Callable, List, Dict, Any

# 메인 라우터 생성
api_router = APIRouter()

# 모든 하위 라우터 가져오기
from app.routers.avatar import router as avatar_router
from app.routers.chat import router as chat_router
from app.routers.camera import router as camera_router
from app.routers.emotion import router as emotion_router
from app.routers.schedule_chat import router as schedule_chat_router


# 모든 라우터 등록하기
api_router.include_router(avatar_router)
api_router.include_router(chat_router)
api_router.include_router(camera_router)
api_router.include_router(emotion_router)
api_router.include_router(schedule_chat_router)


# main.py에서 한 번에 등록할 수 있도록 모든 라우터 내보내기
__all__ = ["api_router"]
