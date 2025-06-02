# core/stt.py
# Whisper로 마이크 입력을 텍스트로 변환하고, 텍스트로부터 감정 + 목소리 억양 감정 추출

import whisper
import sounddevice as sd
import soundfile as sf
import tempfile

from backend.app.emotion.emotion import extract_emotion_from_text
from backend.app.emotion.ser_emotion import analyze_voice_emotion_korean as analyze_voice_emotion

def load_whisper_model(model_size="base"):
    # Whisper 모델 로딩 (기본: base 모델)
    print("🔊 Whisper 모델 로딩 중...")
    return whisper.load_model(model_size)

def transcribe_stream(model, duration=3, fs=16000):
    # 🎙️ 마이크로 음성을 녹음하고 Whisper로 텍스트로 변환하며,
    #    텍스트 감정과 음성 억양 감정을 동시에 추출

    print("🎙️ 음성 녹음 중...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()

    # 임시 wav 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        sf.write(f.name, audio, fs)

        # Whisper로 텍스트 추출
        text = model.transcribe(f.name).get("text", "").strip()

        # 텍스트 기반 감정
        text_emotion = extract_emotion_from_text(text)

        # 목소리 억양 기반 감정
        voice_emotion = analyze_voice_emotion(f.name)

    return text, text_emotion, voice_emotion  # ✅ 세 값을 반환


