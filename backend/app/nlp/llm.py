from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
import os
import logging
from typing import Optional
from ..nlp.response_formatter import format_llm_response
from ..core.mbti_data import MBTI_PERSONAS

# ✨ 전역 Gemini 모델 변수 추가
_gemini_model = None

def configure_gemini():
    # 환경변수에서 Google API 키 가져오기
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY 환경변수가 없습니다.")
    genai.configure(api_key=api_key)
    
    # ✨ 전역 모델 초기화
    global _gemini_model
    try:
        _gemini_model = genai.GenerativeModel('gemini-2.0-flash')
        logging.info("Gemini model initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize Gemini model: {e}")
        raise

async def generate_response(
    emotion: str,
    user_text: str,
    context: dict,
    ai_mbti_persona: Optional[str] = None, # ✨ ai_mbti_persona 인자 추가
    model_name: str = "gemini-2.0-flash"
):
    global _gemini_model
    if _gemini_model is None:
        logging.error("Gemini model is not initialized. Attempting to initialize now (this is not ideal).")
        try:
            configure_gemini()
            if _gemini_model is None: # 재초기화 실패 시
                raise RuntimeError("Failed to re-initialize Gemini model.")
        except Exception as e:
            logging.error(f"Critical error: Gemini model not available for response generation: {e}", exc_info=True)
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
        logging.info(f"Applying AI persona: {mbti_description}")
    else:
        full_persona = f"너는 감정에 공감하고 위로하는 AI야.\n{common_directives}\n"
        logging.info("Applying default AI persona.")
    
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
    logging.info(f"Generated prompt for Gemini: {prompt}") # ✨ 생성된 프롬프트 로깅 (핵심 1)

    try:
        # ✨ Gemini 모델 호출 직전 로깅
        logging.info("Gemini 모델 호출 중...")
        response = await _gemini_model.generate_content_async(prompt)

        # ✨ Gemini 응답 객체 확인 로깅
        logging.info(f"Gemini raw response object type: {type(response)}") # 응답 객체 타입
        logging.info(f"Gemini raw response parts: {response.parts if hasattr(response, 'parts') else 'N/A'}") # 응답 parts
        logging.info(f"Gemini raw response text: {response.text.strip()}") # ✨ 실제 텍스트 응답 (핵심 2)

        # 응답 텍스트만 반환
        return response.text.strip().replace("[분할]", "\n")
    except Exception as e:
        logging.error(f"LLM 응답 생성 중 오류 발생: {e}", exc_info=True)
        return "죄송합니다, 현재 응답을 생성할 수 없습니다."

# ✨ 기존 함수와의 호환성을 위한 래퍼 함수
def generate_response_sync(
    face_emotion: str,
    voice_emotion: str,
    scene: str,
    user_text: str,
    context: dict,
    model_name="gemini-2.0-flash",
    vlm_analysis: str = None,
    ai_mbti_persona: Optional[str] = None
):
    """
    기존 코드와의 호환성을 위한 동기 래퍼 함수
    """
    import asyncio
    
    # 감정 합성 (기존 로직 유지)
    emotion = face_emotion  # 간단한 처리, 필요시 더 복잡한 로직 적용
    
    # VLM 분석 결과가 있는 경우 컨텍스트에 추가
    if vlm_analysis:
        context["vlm_analysis"] = vlm_analysis
    
    # 비동기 함수 호출
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 이미 실행 중인 루프가 있으면 새 스레드에서 실행
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, generate_response(
                    emotion=emotion,
                    user_text=user_text,
                    context=context,
                    ai_mbti_persona=ai_mbti_persona,
                    model_name=model_name
                ))
                return future.result()
        else:
            return asyncio.run(generate_response(
                emotion=emotion,
                user_text=user_text,
                context=context,
                ai_mbti_persona=ai_mbti_persona,
                model_name=model_name
            ))
    except Exception as e:
        logging.error(f"Error in generate_response_sync: {str(e)}")
        return "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다."

def generate_search_summary(user_text: str, raw_results: list[str]) -> str:
    print("🔍 검색 요약 생성")
    combined = "\n\n".join(raw_results)
    prompt = (
        f"너는 정보 검색 결과를 요약 및 번역해주는 전문 AI야.\n\n"
        f"사용자의 질문은 다음과 같아:\n"
        f"\"{user_text}\"\n\n"
        f"검색 결과는 아래와 같아:\n"
        f"{combined}\n\n"
        "이 검색 결과들을 항목별로 정돈해서 요약하고, 이해하기 쉽게 한국어로 번역해줘. "
        "카테고리(예: 유선 키보드, 무선 키보드 등) 별로 정리하면 더 좋아."
    )

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.7,
            api_key=os.getenv("GOOGLE_API_KEY"),
        )
        response = llm.invoke(prompt)
        return format_llm_response(response)
    except Exception as e:
        logging.error(f"Error in generate_search_summary: {str(e)}")
        return "죄송합니다. 검색 결과를 요약하는 중에 오류가 발생했습니다."

