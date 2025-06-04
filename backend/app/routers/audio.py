from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
from app.audio.stt import router as stt_router  # 올바른 경로로 수정
from app.audio.tts import router as tts_router  # 올바른 경로로 수정

app = FastAPI()  # FastAPI 앱 생성

router = APIRouter(
    prefix="/api",
    tags=["ai_response"]
)

class AIResponse(BaseModel):
    text: str
    sender: str

@router.post("/ai-response")
async def save_ai_response(response: AIResponse):
    """
    프론트엔드에서 전송된 AI 응답을 처리하는 엔드포인트.
    """
    # 예: 응답을 로그로 저장하거나 데이터베이스에 저장
    print(f"AI 응답 저장: {response.text} (보낸 사람: {response.sender})")
    return {"message": "AI 응답이 성공적으로 저장되었습니다."}

router.include_router(stt_router)
router.include_router(tts_router)

app.include_router(router)  # 라우터를 FastAPI 앱에 등록