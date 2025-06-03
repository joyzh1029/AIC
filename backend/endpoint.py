from fastapi import FastAPI
from voice.stt import router as stt_router
from voice.tts import router as tts_router

app = FastAPI()
app.include_router(stt_router)
app.include_router(tts_router)
