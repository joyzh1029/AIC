# backend/stt/whisper_api.py

from fastapi import APIRouter, UploadFile, File
from faster_whisper import WhisperModel
import tempfile, shutil, os

# 1. 이 모듈만을 위한 FastAPI 라우터 인스턴스 생성
router = APIRouter()  # 다른 FastAPI app과 분리하여 라우팅 용도로 사용

# 2. Whisper 모델을 서버 시작 시 1회 메모리에 로드
# - "base" 모델 (가벼움/빠름)
# - device="cuda": GPU 사용, 없으면 "cpu"로 변경
# - compute_type="float16": 연산 속도 향상(GPU)
model = WhisperModel("base", device="cuda", compute_type="float16")

@router.post("/api/stt")
async def stt_inference(audio: UploadFile = File(...)):
    """
    Whisper 기반 음성(STT) 변환 API.
    프론트엔드에서 FormData로 음성 녹음 파일을 전송하면,
    Whisper 모델로 텍스트 변환 결과를 반환한다.
    응답 예시: {"result": "텍스트 변환 결과"}
    """
    # 1. 업로드된 음성 파일을 임시 파일로 저장 (.wav 확장자)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        shutil.copyfileobj(audio.file, tmp)  # 파일 객체를 복사해 임시 파일에 저장
        tmp_path = tmp.name  # 임시 파일 경로 기억

    try:
        # 2. Whisper 모델로 음성파일을 텍스트로 변환
        segments, _ = model.transcribe(tmp_path)
        # segments: 인식된 텍스트 구간들의 리스트
        # 예: [Segment(text="안녕하세요", ...), ...]
        full_text = " ".join([seg.text for seg in segments])  # 전체 텍스트 합치기

        # 3. 변환된 텍스트를 JSON 형태로 반환
        return {"result": full_text}

    finally:
        # 4. 임시 파일 삭제(메모리/디스크 낭비 방지)
        os.remove(tmp_path)
