# core/llm.py
# 구글 Gemini API를 사용하여 감정 기반 응답을 생성함

import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import logging

from app.core.mbti_data import MBTI_PERSONAS # ✨ MBTI_PERSONAS 임포트

# 로거 설정 (선택 사항, 하지만 디버깅에 유용)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()           # .env 파일에서 API 키 로딩
_gemini_model = None    # _gemini_model 전역 변수 선언

def configure_gemini():
    """
    Gemini API 키를 구성하고, GenerativeModel 인스턴스를 전역으로 초기화합니다.
    이 함수는 FastAPI 애플리케이션의 시작 시점에 단 한 번 호출되어야 합니다.
    """
    global _gemini_model # ✨ 전역 변수임을 명시

    # 환경변수에서 Google API 키 가져오기
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
        raise ValueError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
    
    genai.configure(api_key=api_key)
    logger.info("Gemini API 구성 성공.")

    try:
        _gemini_model = genai.GenerativeModel("gemini-2.0-flash")
        logger.info("Gemini 2.0 Flash 모델 로드 성공.")
    except Exception as e:
        logger.error(f"로드에 실패함. Gemini model: {e}", exc_info=True)
        raise RuntimeError(f"로드에 실패함. Gemini model: {e}") from e

async def generate_response(
    emotion: str,
    user_text: str,
    context: dict,
    ai_mbti_persona: Optional[str] = None, # ✨ ai_mbti_persona 인자 추가
    model_name: str = "gemini-2.0-flash"
):
    global _gemini_model
    if _gemini_model is None:
        logger.error("Gemini model is not initialized. Attempting to initialize now (this is not ideal).")
        try:
            configure_gemini()
            if _gemini_model is None: # 재초기화 실패 시
                raise RuntimeError("Failed to re-initialize Gemini model.")
        except Exception as e:
            logger.error(f"Critical error: Gemini model not available for response generation: {e}", exc_info=True)
            return "죄송합니다, AI 모델을 초기화할 수 없어 응답을 생성할 수 없습니다."
    
    # ✨ 공통 지시사항 정의
    common_directives = (
        "친구와의 일상적인 대화처럼 간결하고 직접적인 반말 투로 소통해.\n"
        "답변은 2-3개의 짧은 문장으로 나누어 보내며 각 문장 사이에 [분할]이라는 구분자를 넣어."
    )

    # ✨ MBTI 페르소나 적용 (ai_mbti_persona가 제공되면 추가)
    if ai_mbti_persona:
        mbti_description = MBTI_PERSONAS.get(ai_mbti_persona, f"{ai_mbti_persona}")
        full_persona = f"{mbti_description}\n{common_directives}\n"
        logger.info(f"Applying AI persona: {mbti_description}")
    else:
        full_persona = f"너는 감정에 공감하고 위로하는 AI야.\n{common_directives}\n"
        logger.info("Applying default AI persona.")
    
    # 사용자의 감정 상태, 발화, 컨텍스트 정보를 기반으로 프롬프트 구성
    prompt = (
        f"{full_persona}\n"
        f"사용자는 현재 '{emotion}' 상태야.\n"
        f"사용자의 발화 내용은: \"{user_text}\"\n\n"
        f"날씨: {context.get('weather', '알 수 없음')}\n"
        f"수면 시간: {context.get('sleep', '알 수 없음')}\n"
        f"스트레스 수준: {context.get('stress', '알 수 없음')}\n"
        f"최근 감정 흐름: {context.get('emotion_history', [])}\n\n"
        "위 정보를 바탕으로 위로 혹은 공감의 한 마디를 자연스럽고 인간적으로 전달해줘.\n"
        "가볍게 질문 하나로 마무리해도 좋아."
    )
    logger.info(f"Generated prompt for Gemini: {prompt}") # ✨ 생성된 프롬프트 로깅 (핵심 1)

    try:
        # ✨ Gemini 모델 호출 직전 로깅
        logger.info("Gemini 모델 호출 중...")
        response = await _gemini_model.generate_content_async(prompt)

        # ✨ Gemini 응답 객체 확인 로깅
        logger.info(f"Gemini raw response object type: {type(response)}") # 응답 객체 타입
        logger.info(f"Gemini raw response parts: {response.parts if hasattr(response, 'parts') else 'N/A'}") # 응답 parts
        logger.info(f"Gemini raw response text: {response.text.strip()}") # ✨ 실제 텍스트 응답 (핵심 2)

        # 응답 텍스트만 반환
        return response.text.strip()
    except Exception as e:
        logging.error(f"LLM 응답 생성 중 오류 발생: {e}", exc_info=True)
        return "죄송합니다, 현재 응답을 생성할 수 없습니다."
