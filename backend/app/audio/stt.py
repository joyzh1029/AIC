# core/stt.py
# Whisper로 마이크 입력을 텍스트로 변환 (STT 전용)

import whisper
import sounddevice as sd
import soundfile as sf
import tempfile
import torch

# Whisper 모델 로딩 함수
def load_whisper_model(model_size="base"):
    print("🔊 Whisper 모델 로딩 중...")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(model_size, device=device)

    if device == "cuda":
        print("⚡ GPU(FP16) 모드로 Whisper 실행")
        model = model.to("cuda")
    else:
        print("🖥️ CPU(FP32) 모드로 Whisper 실행")

    return model

# 마이크로부터 음성 녹음하고 파일 경로 반환
def record_audio(duration=3, fs=16000):
    print("🎙️ 음성 녹음 중...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        sf.write(f.name, audio, fs)
        return f.name  # 파일 경로 반환

# 주어진 음성 파일로부터 텍스트 추출
def transcribe_audio(model, file_path):
    return model.transcribe(file_path).get("text", "").strip()
