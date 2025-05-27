# llm_module.py

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def configure_gemini():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
    genai.configure(api_key=api_key)

def generate_response(emotion: str, user_text: str, context: dict, model_name="gemini-2.0-flash") -> str:
    prompt = f"""
너는 감정에 공감하고 위로하는 AI야.
사용자는 현재 '{emotion}' 상태야.
사용자의 발화 내용은: "{user_text}"

날씨: {context.get("weather", "알 수 없음")}
수면 시간: {context.get("sleep", "알 수 없음")}
스트레스 수준: {context.get("stress", "알 수 없음")}
최근 감정 흐름: {context.get("emotion_history", [])}

위 정보를 바탕으로 위로 혹은 공감의 한 마디를 자연스럽고 인간적으로 전달해줘.
가볍게 질문 하나로 마무리해도 좋아.
"""

    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text.strip()
