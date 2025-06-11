# backend/app/routers/api.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

# Assuming these imports are correct based on your project structure
from app.core.dependencies import get_current_active_user # 사용자 인증이 필요한 경우
from app.nlp.llm import generate_response # ✨ Gemini 응답 함수 임포트

logger = logging.getLogger(__name__)
api_router = APIRouter() # Assuming this is your main API router instance


class ChatMessage(BaseModel):
    message: str
    user_mbti: Optional[str] = None # MBTI 정보를 프론트엔드에서 보낼 경우
    ai_mbti: Optional[str] = None # AI MBTI 정보를 프론트엔드에서 보낼 경우
    # ✨ 만약 프론트에서 감정 정보를 함께 보낸다면 여기에 추가
    # emotion: Optional[str] = None

class CameraCaptureResponse(BaseModel):
    success: bool
    message: str
    image: Optional[str] = None # Base64 encoded image string
    emotion: Optional[str] = None # Detected emotion


# ✨ 새로운 채팅 엔드포인트 추가
@api_router.post("/chat")
async def chat_with_ai(chat_message: ChatMessage): #, current_user: Dict[str, Any] = Depends(get_current_active_user)): # 인증이 필요하면 주석 해제
    logger.info(f"[/chat] endpoint called with message: {chat_message.message}") # ✨ 추가
    """
    사용자 메시지를 받아 AI 친구 (Gemini)로부터 응답을 생성합니다.
    """
    try:
        # 1. user_text (사용자 발화): chat_message.message를 사용합니다.
        user_text = chat_message.message

        # 2. emotion (사용자 감정):
        # 현재 chat_message에는 emotion 필드가 직접 없음.
        # - 만약 ChatMessage에 emotion 필드를 추가했다면:
        #   user_emotion = chat_message.emotion if chat_message.emotion else "알 수 없음"
        # - 지금은 임시로 기본값을 사용합니다. 실제로는 감정 분석 결과나 이전 대화에서 가져와야 합니다.
        user_emotion = "보통" # ✨ 임시 기본값. 실제로는 동적으로 가져와야 함.
        # 또는, 만약 카메라 캡처 시 감지된 감정을 어딘가 저장해두고 사용할 수 있다면 그 값을 사용합니다.
        # 예: user_emotion = some_emotion_from_previous_capture

        # 3. context (컨텍스트 정보):
        # 현재 chat_message에는 context 필드가 직접 없음.
        # - 임시로 빈 딕셔너리 또는 고정된 기본값을 사용합니다.
        # - 실제로는 사용자 ID 등을 기반으로 데이터베이스에서 조회하거나 다른 API를 통해 가져와야 합니다.
        user_context = { # ✨ 임시 컨텍스트. 실제로는 동적으로 생성되어야 함.
            "weather": "알 수 없음",
            "sleep": "알 수 없음",
            "stress": "알 수 없음",
            "emotion_history": []
        }
        # 만약 사용자와 AI의 MBTI를 컨텍스트에 포함하고 싶다면:
        if chat_message.user_mbti:
            user_context["user_mbti"] = chat_message.user_mbti
        if chat_message.ai_mbti:
            user_context["ai_mbti"] = chat_message.ai_mbti

        # 4. ai_mbti_persona (선택 사항): chat_message.ai_mbti를 사용합니다.
        ai_mbti_persona = chat_message.ai_mbti # ✨ AI MBTI 페르소나 설정 (선택 사항)

        logger.info(f"Preparing to call generate_response with:") # ✨ 추가
        logger.info(f"  emotion: {user_emotion}") # ✨ 추가
        logger.info(f"  user_text: {user_text}") # ✨ 추가
        logger.info(f"  context: {user_context}") # ✨ 추가
        logger.info(f"  ai_mbti_persona: {ai_mbti_persona}") # ✨ 추가

        # Gemini 모델에게 메시지 전달 및 응답 받기
        ai_response = await generate_response(
            emotion=user_emotion,
            user_text=user_text,
            context=user_context,
            ai_mbti_persona=ai_mbti_persona # 선택 사항이므로, None이면 함수 내부에서 기본 페르소나 사용
        )
        logger.info(f"Received AI response from generate_response: {ai_response[:50]}...") # ✨ 추가 (앞부분만)

        return {"response": ai_response}
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True) # ✨ exc_info=True로 스택 트레이스 출력
        raise HTTPException(status_code=500, detail="AI 응답 생성 중 오류가 발생했습니다.")

# 기존 카메라 관련 엔드포인트 (ChatPage.tsx에서 호출하는 부분)
# 이 부분은 이미 존재한다고 가정하고 있습니다. 필요하다면 내용을 붙여 넣어주세요.
# @api_router.post("/camera/start")
# async def start_camera_endpoint():
#     # ... (기존 카메라 시작 로직)
#     return {"message": "Camera started"}

# @api_router.post("/camera/stop")
# async def stop_camera_endpoint():
#     # ... (기존 카메라 중지 로직)
#     return {"message": "Camera stopped"}

# @api_router.post("/camera/capture", response_model=CameraCaptureResponse)
# async def capture_photo_endpoint():
#     # ... (기존 사진 촬영 로직)
#     return {"success": True, "message": "Photo captured", "image": "base64_image_data", "emotion": "happy"}

# TTS 엔드포인트 (ChatPage.tsx에서 호출하는 부분)
# @api_router.post("/api/tts")
# async def tts_endpoint(tts_request: Dict[str, str]):
#     # ... (기존 TTS 로직)
#     pass # 실제 TTS 구현은 해당 모듈에 있을 것입니다.