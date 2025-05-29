from fastapi import FastAPI, UploadFile, File
from faster_whisper import WhisperModel
import tempfile
import shutil
import os

app = FastAPI()
model = WhisperModel("base", device="cuda", compute_type="float16")  # device, 모델 크기 선택 가능

@app.post("/api/stt")
async def transcribe(audio: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        shutil.copyfileobj(audio.file, tmp)
        tmp_path = tmp.name
    try:
        segments, _ = model.transcribe(tmp_path)
        full_text = " ".join([seg.text for seg in segments])
        return {"result": full_text}
    finally:
        os.remove(tmp_path)
