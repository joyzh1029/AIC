from fastapi import APIRouter, UploadFile, File
from dotenv import load_dotenv
import os
import tempfile
import whisper

load_dotenv()
whisper_model = whisper.load_model("base")

router = APIRouter(
    prefix="/api",    # prefix는 실제 주소에 맞춰 수정
    tags=["stt"]
)

@router.post("/stt")
async def stt_api(audio: UploadFile = File(...)):
    # 업로드된 음성 파일을 임시 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as f:
        content = await audio.read()
        f.write(content)
        audio_path = f.name

    try:
        # whisper로 한국어 STT 처리
        stt_result = whisper_model.transcribe(audio_path, language="ko")["text"].strip()
        return {"result": stt_result}
    finally:
        # 임시 파일 삭제
        os.unlink(audio_path)
