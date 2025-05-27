# main.py
from smol_vlm_module import load_smol_vlm, analyze_face_emotion
from stt_module import load_whisper_model, transcribe, record_audio_to_file
from emotion_core import extract_emotion_from_text, extract_emotion_from_vlm, synthesize_emotion
from llm_module import configure_gemini, generate_response

from PIL import Image

def main():
    try:
        processor, model, device = load_smol_vlm()
        whisper_model = load_whisper_model()
        configure_gemini()
    except Exception as e:
        print(f"❌ 모델 로딩 실패: {e}")
        return

    try:
        image = Image.open("data/sample_face2.jpg").convert("RGB")
    except FileNotFoundError:
        print("❌ 이미지 파일을 찾을 수 없습니다.")
        return

    audio_path = record_audio_to_file("data/temp.wav")

    try:
        face_text = analyze_face_emotion(image, processor, model, device)
        user_text = transcribe(audio_path, whisper_model)
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")
        return

    face_emotion = extract_emotion_from_vlm(face_text)
    voice_emotion = extract_emotion_from_text(user_text)
    final_emotion = synthesize_emotion(face_emotion, voice_emotion)

    context = {
        "weather": "흐림",
        "sleep": "4시간",
        "stress": "높음",
        "emotion_history": ["sad", "neutral", "sad"]
    }

    try:
        response = generate_response(final_emotion, user_text, context)
    except Exception as e:
        response = f"(응답 생성 실패: {e})"

    print("\n[결과]")
    print("🖼️ 얼굴 감정 설명:", face_text)
    print("🧠 얼굴 감정:", face_emotion)
    print("🗣️ 텍스트:", user_text)
    print("💡 최종 감정:", final_emotion)
    print("🤖 Gemini 응답:", response)

if __name__ == "__main__":
    main()
