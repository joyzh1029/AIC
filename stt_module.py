# stt_module.py
import whisper
import sounddevice as sd
import soundfile as sf

def load_whisper_model(model_size="base"):
    print(f"📦 Whisper 모델 로딩 중: {model_size}")
    return whisper.load_model(model_size)

def transcribe(audio_path, model):
    print(f"🧠 STT 분석 시작 → 파일: {audio_path}")
    result = model.transcribe(audio_path)
    return result.get("text", "").strip()

# (선택) 녹음 테스트용
def record_audio_to_file(filename="temp.wav", duration=5, fs=16000):
    print("🎙 음성 녹음 중...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    sf.write(filename, audio, fs)
    print(f"✅ 녹음 완료: {filename}")
    return filename
