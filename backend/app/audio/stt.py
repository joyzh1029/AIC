# app/audio/stt.py
# Whisper로 마이크 입력을 텍스트로 변환하고, 목소리 억양 감정을 추출

import whisper
import sounddevice as sd
import soundfile as sf
import tempfile
import torch

from app.emotion.ser_emotion import analyze_voice_emotion_korean as analyze_voice_emotion

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

def transcribe_stream(model, duration=3, fs=16000):
    print("🎙️ 음성 녹음 중...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        sf.write(f.name, audio, fs)

        text = model.transcribe(f.name).get("text", "").strip()
        voice_emotion = analyze_voice_emotion(f.name)

    return text, voice_emotion
