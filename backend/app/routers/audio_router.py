from fastapi import APIRouter, Form, File, Body
from pydantic import BaseModel
from app.audio import tts, stt

class TTSRequest(BaseModel):
    text: str
    speaker: str = "ko"

router = APIRouter(
    prefix="/api/audio",
    tags=["audio"]
)

@router.post("/tts")
async def text_to_speech_endpoint(request: TTSRequest):
    """TTS 엔드포인트"""
    return await tts.text_to_speech(request.text)

@router.post("/stt")
async def speech_to_text_endpoint(audio = File(...)):
    """STT 엔드포인트"""
    return await stt.stt_api(audio)