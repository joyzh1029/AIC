# backend/TTS/tts.py

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS (프론트엔드 개발 환경에서 접근 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/stt")
async def transcribe(audio: UploadFile = File(...)):
    # 여기에 Whisper 등 음성인식 처리 코드 작성
    # 임시 예시:
    contents = await audio.read()
    # 실제로는 파일 저장 후 처리
    return {"result": "여기에 음성 인식 결과"}
