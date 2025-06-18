# core/stt.py
# Whisper로 마이크 입력을 텍스트로 변환 (STT 전용)

import whisper
import sounddevice as sd
import soundfile as sf
import tempfile
import torch
import logging
import os

# 로거 설정
logger = logging.getLogger(__name__)

# Whisper 모델 로딩 함수
def load_whisper_model(model_size="base"):
    logger.info("🔊 Whisper 모델 로딩 중...")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(model_size, device=device)

    if device == "cuda":
        logger.info("⚡ GPU(FP16) 모드로 Whisper 실행")
        model = model.to("cuda")
    else:
        logger.info("🖥️ CPU(FP32) 모드로 Whisper 실행")

    return model

# 마이크로부터 음성 녹음하고 파일 경로 반환
def record_audio(duration=3, fs=16000):
    logger.info("🎙️ 음성 녹음 중...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        sf.write(f.name, audio, fs)
        return f.name  # 파일 경로 반환

# 주어진 음성 파일로부터 텍스트 추출
def transcribe_audio(model, file_path):
    try:
        logger.info(f"음성 파일 변환 시작: {file_path}")
        
        # 파일 존재 확인
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"음성 파일을 찾을 수 없습니다: {file_path}")
            
        # 파일 크기 확인
        file_size = os.path.getsize(file_path)
        logger.info(f"음성 파일 크기: {file_size} bytes")
        
        if file_size == 0:
            raise ValueError("음성 파일이 비어있습니다")
            
        # Whisper 모델로 음성 인식 수행
        result = model.transcribe(file_path)
        
        # 결과 검증
        text = result.get("text", "").strip()
        if not text:
            logger.warning("음성 인식 결과가 비어있습니다")
            return ""
            
        logger.info(f"음성 인식 결과: {text}")
        return text
        
    except Exception as e:
        logger.error(f"음성 인식 중 오류 발생: {str(e)}")
        raise RuntimeError(f"음성 인식 실패: {str(e)}")

