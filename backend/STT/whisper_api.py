# backend/stt/whisper_api.py
from fastapi import APIRouter, UploadFile, File
from faster_whisper import WhisperModel
import tempfile, shutil, os

router = APIRouter()  # 이 모듈만의 라우터

# 모델은 서버 시작시 1회만 메모리에 로드
model = WhisperModel("base", device="cuda", compute_type="float16")  # CPU 사용시 "cpu"

@router.post("/api/stt")
async def stt_inference(audio: UploadFile = File(...)):
    """
    Whisper 기반 음성(STT) 변환 API.
    - 프론트엔드에서 FormData로 녹음 파일 전송시 사용
    - 응답: {"result": 변환텍스트}
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        shutil.copyfileobj(audio.file, tmp)
        tmp_path = tmp.name
    try:
        segments, _ = model.transcribe(tmp_path)
        full_text = " ".join([seg.text for seg in segments])
        return {"result": full_text}
    finally:
        os.remove(tmp_path)
