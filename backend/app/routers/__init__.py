"""
API 라우터 모듈
이 모듈은 모든 API 라우트를 중앙 집중식으로 관리하고 등록하는 역할을 합니다
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Callable, List, Dict, Any

# 메인 라우터 생성
api_router = APIRouter()

# chat_router
from app.routers.chat import router as chat_router
api_router.include_router(chat_router)

from app.routers.emotion import router as emotion_router
api_router.include_router(emotion_router)

from app.routers.schedule_chat import router as schedule_chat_router
from app.routers.mbti import router as mbti_router
from app.routers.user import router as user_router
from app.routers.avatar import router as avatar_router
# from app.routers.search import router as search_router # 주석 처리된 search_router는 현재 사용하지 않음

api_router.include_router(emotion_router)
api_router.include_router(schedule_chat_router)
api_router.include_router(mbti_router)
api_router.include_router(user_router)
api_router.include_router(avatar_router)
# api_router.include_router(search_router)

# main.py에서 한 번에 등록할 수 있도록 모든 라우터 내보내기
__all__ = ["api_router"]