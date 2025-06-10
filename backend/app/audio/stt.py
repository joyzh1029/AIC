from fastapi import UploadFile, File
from dotenv import load_dotenv
import os
import tempfile
import whisper

load_dotenv()
whisper_model = whisper.load_model("base")

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

def transcribe_stream(audio_path: str, language: str = "ko") -> str:
    """
    파일 경로를 받아 Whisper로 음성 인식 결과(텍스트)를 반환합니다.
    """
    result = whisper_model.transcribe(audio_path, language=language)
    return result["text"].strip()

def load_whisper_model(model_size: str = "base"):
    """
    Whisper 모델을 로드하여 반환합니다.
    """
    return whisper.load_model(model_size)
