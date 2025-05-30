# core/llm.py
# 구글 Gemini API를 사용하여 감정 기반 응답을 생성함

import os
import google.generativeai as genai
from dotenv import load_dotenv

# .env 파일에서 API 키 로딩
load_dotenv()

def configure_gemini():
    # 환경변수에서 Google API 키 가져오기
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY 환경변수가 없습니다.")
    genai.configure(api_key=api_key)

def generate_response(face_emotion, voice_emotion, scene, user_text, context, model_name="gemini-2.0-flash"):
    # 사용자의 감정 상태, 발화, 컨텍스트 정보를 기반으로 프롬프트 구성
    prompt = (
        f"너는 감정에 공감하고 위로하는 AI야.\n"
        f"사용자는 현재 이런 상태야:\n"
        f"- 표정 감정: '{face_emotion}'\n"
        f"- 목소리 감정: '{voice_emotion}'\n"
        f"- 주변 환경은 다음과 같아: '{scene}'\n"
        f"발화 내용: \"{user_text}\"\n\n"
        f"날씨: {context.get('weather', '알 수 없음')}\n"
        f"수면 시간: {context.get('sleep', '알 수 없음')}\n"
        f"스트레스 수준: {context.get('stress', '알 수 없음')}\n"
        f"최근 감정 흐름: {context.get('emotion_history', [])}\n\n"
        "위 정보를 바탕으로 인간적인 위로 또는 공감의 메시지를 만들어줘.\n"
        "마무리로 가벼운 질문 하나도 곁들이면 좋아."
    )

    # Gemini 모델 호출
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)

    # 응답 텍스트만 반환
    return response.text.strip()

