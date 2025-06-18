from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import io
import os
import httpx
from pydantic import BaseModel

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")

router = APIRouter(
    prefix="/api/tts",
    tags=["tts"]
)

# POST 요청용 데이터 모델
class TTSRequest(BaseModel):
    text: str
    voice_id: str = "Korean_WiseElf"
    speed: float = 1.0
    vol: float = 1.0
    audio_sample_rate: int = 24000
    bitrate: int = 128000
    format: str = "mp3"

@router.post("")
async def tts_post(request: TTSRequest):
    if not MINIMAX_API_KEY:
        raise HTTPException(status_code=500, detail="MINIMAX_API_KEY가 설정되지 않았습니다.")

    if not request.text.strip():
        raise HTTPException(status_code=400, detail="텍스트를 입력해주세요.")

    payload = {
        "model": "speech-02-hd",
        "text": request.text,
        "voice_id": request.voice_id,
        "speed": request.speed,
        "vol": request.vol,
        "audio_sample_rate": request.audio_sample_rate,
        "bitrate": request.bitrate,
        "format": request.format
    }

    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://api.minimax.chat/v1/text_to_speech", json=payload, headers=headers)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Minimax 오류: {response.text}"
                )

            return StreamingResponse(
                io.BytesIO(response.content),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": "inline; filename=speech.mp3",
                    "Cache-Control": "no-cache"
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 처리 실패: {str(e)}")

@router.get("/generate")
async def generate_tts(
    text: str = Query(..., description="TTS로 변환할 텍스트입니다."),
    voice_id: str = "female-tianmei-jingpin",
    speed: float = 1.0,
    vol: float = 1.0,
    audio_sample_rate: int = 24000,
    bitrate: int = 128000,
    format: str = "mp3"
):
    """
    Minimax TTS API를 사용하여 입력 텍스트를 음성(mp3)으로 변환합니다.
    """
    if not MINIMAX_API_KEY:
        raise HTTPException(status_code=500, detail="MINIMAX_API_KEY가 설정되지 않았습니다.")

    if not text.strip():
        raise HTTPException(status_code=400, detail="텍스트를 입력해주세요.")

    payload = {
        "model": "speech-02-hd",
        "text": text,
        "voice_id": voice_id,
        "speed": speed,
        "vol": vol,
        "audio_sample_rate": audio_sample_rate,
        "bitrate": bitrate,
        "format": format
    }

    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://api.minimax.chat/v1/text_to_speech", json=payload, headers=headers)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Minimax 오류: {response.text}"
                )

            return StreamingResponse(
                io.BytesIO(response.content),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": "inline; filename=speech.mp3",
                    "Cache-Control": "no-cache"
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 처리 실패: {str(e)}")