from fastapi import FastAPI
from stt.stt_to_chat import router as stt_to_chat_router  # 실시간 대화용 라우터
from stt.stt import router as stt_router                  # 일반 STT용 라우터

app = FastAPI()
app.include_router(stt_router)  # 엔드포인트 등록
