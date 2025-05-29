import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS (생략 가능)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 현재 tts.py의 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# tts_audio/example.mp3의 절대 경로 이후 api연결시엔 이 코드를 변경해야 함
AUDIO_PATH = os.path.join(BASE_DIR, "tts_audio", "example.mp3")

@app.post("/api/tts")
def get_example_audio():
    # 파일 존재 여부 확인 (없으면 404)
    if not os.path.exists(AUDIO_PATH):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="오디오 파일을 찾을 수 없습니다.")
    return FileResponse(AUDIO_PATH, media_type="audio/mp3", filename="example.mp3")
