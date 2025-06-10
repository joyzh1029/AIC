from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
import time
import asyncio
import logging

from app.nlp.llm import generate_response
from app.emotion.synthesizer import synthesize_emotion_3way

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[float] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    user_id: str
    ai_id: str
    context: Optional[Dict[str, Any]] = None

@router.post("")
async def chat_endpoint(request: ChatRequest):
    try:
        # 기본 컨텍스트 설정
        context = request.context or {
            "weather": "맑음",
            "sleep": "7시간",
            "stress": "중간",
            "location_scene": "실내, 책상 앞",
            "emotion_history": ["neutral", "neutral", "neutral"]
        }
        
        # 사용자 메시지 추출
        user_messages = [msg.content for msg in request.messages if msg.role == "user"]
        user_text = user_messages[-1] if user_messages else ""
        
        # 감정 합성 - 세 방향 감정 합성 함수 사용
        # 여기서는 예시로 기본값을 사용하지만, 실제 응용에서는 컨텍스트나 분석에서 가져와야 함
        face_emotion = context.get("face_emotion", "neutral")
        text_emotion = context.get("text_emotion", "neutral")
        voice_emotion = context.get("voice_emotion", "neutral")
        emotion = synthesize_emotion_3way(face_emotion, text_emotion, voice_emotion)
        
        # 응답 생성
        response_text = generate_response(emotion, user_text, context)
        
        # 응답 구성
        return JSONResponse(content={
            "success": True,
            "response": response_text,
            "emotion": emotion
        })
    except Exception as e:
        logging.error(f"Chat endpoint error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
