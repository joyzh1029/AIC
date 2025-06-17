from fastapi import APIRouter, Request, HTTPException, UploadFile, File
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
from app.core.mbti_data import MBTI_PERSONAS, MBTI_COMPATIBILITY # mbti_data.py에서 임포트

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[float] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    user_id: str
    ai_id: str
    user_mbti: Optional[str] = None # ✨ 사용자 MBTI 추가
    relationship_type: Optional[str] = None # ✨ 관계 유형(동질적 or 보완적) 추가
    ai_name: Optional[str] = None # ✨ AI 친구 이름
    generated_image_url: Optional[str] = None # ✨ 생성된 AI 이미지 URL (백엔드에서 사용하진 않지만 프론트엔드에서 전달)
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

        # ✨ 1. 사용자 MBTI 및 관계 유형 유효성 검사 및 AI MBTI 결정
        user_mbti = request.user_mbti
        relationship_type = request.relationship_type

        if not user_mbti or not relationship_type:
            raise HTTPException(
                status_code=400,
                detail="User MBTI and relationship type are required."
            )

        ai_mbti = MBTI_COMPATIBILITY.get(user_mbti, {}).get(relationship_type)

        if not ai_mbti:
            raise HTTPException(
                status_code=400,
                detail=f"Could not determine AI MBTI for user_mbti: {user_mbti} and relationship_type: {relationship_type}"
            )

        ai_persona_text = MBTI_PERSONAS.get(ai_mbti, "당신은 사용자에게 공감하고 위로하는 AI입니다.")
        logging.info(f"Determined AI MBTI: {ai_mbti}, Persona: {ai_persona_text}")


        # 감정 합성 - 세 방향 감정 합성 함수 사용
        # 여기서는 예시로 기본값을 사용하지만, 실제 응용에서는 컨텍스트나 분석에서 가져와야 함
        face_emotion = context.get("face_emotion", "neutral")
        text_emotion = context.get("text_emotion", "neutral")
        voice_emotion = context.get("voice_emotion", "neutral")
        emotion = synthesize_emotion_3way(face_emotion, text_emotion, voice_emotion)
        logging.info(f"Synthesized emotion for LLM: {emotion}")


        # 응답 생성
        response_text = generate_response(
            face_emotion,
            voice_emotion,
            context.get("location_scene", "실내, 책상 앞"),
            user_text,
            context
        )
        logging.info(f"LLM generated response: {response_text}")

        # 응답 구성
        return JSONResponse(content={
            "success": True,
            "response": response_text,
            "emotion": emotion,
            "ai_mbti": ai_mbti,       # 결정된 AI의 MBTI
            "ai_persona": ai_persona_text, # AI의 적용된 페르소나
        })
    except Exception as e:
        logging.error(f"Chat endpoint error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.post("/upload")
async def upload_image(image: UploadFile = File(...)):
    try:
        content = await image.read()
        # 确保保存目录存在
        save_dir = os.path.join("static", "uploads")
        os.makedirs(save_dir, exist_ok=True)
        # 生成唯一文件名
        filename = f"img_{int(time.time())}_{image.filename}"
        save_path = os.path.join(save_dir, filename)
        with open(save_path, "wb") as f:
            f.write(content)
        # 返回图片的相对路径
        return JSONResponse(content={"success": True, "message": "이미지 업로드 성공", "image_url": f"/static/uploads/{filename}"})
    except Exception as e:
        logging.error(f"Image upload error: {str(e)}")
        return JSONResponse(status_code=500, content={"success": False, "message": "이미지 업로드 실패", "error": str(e)})
