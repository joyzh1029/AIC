from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
import os
import logging
from app.nlp.response_formatter import format_llm_response

def configure_gemini():
    # 환경변수에서 Google API 키 가져오기
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY 환경변수가 없습니다.")
    genai.configure(api_key=api_key)

def generate_response(
    face_emotion: str,
    voice_emotion: str,
    scene: str,
    user_text: str,
    context: dict,
    model_name="gemini-2.0-flash"
):
    if "search_raw_list" in context:
        print("🔍 검색 응답 생성")
        raw_list = context["search_raw_list"]
        combined = "\n\n".join(raw_list)
        prompt = (
            f"너는 정보 검색 결과를 요약 및 번역해주는 전문 AI야.\n\n"
            f"사용자의 질문은 다음과 같아:\n"
            f"\"{user_text}\"\n\n"
            f"검색 결과는 아래와 같아:\n"
            f"{combined}\n\n"
            "이 검색 결과들을 항목별로 정돈해서 요약하고, 이해하기 쉽게 한국어로 번역해줘. "
            "카테고리(예: 유선 키보드, 무선 키보드 등) 별로 정리하면 더 좋아."
        )
    else:
        print("💬 감정 응답 생성")
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

    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.7,
            api_key=os.getenv("GEMINI_API_KEY"),
        )
        response = llm.invoke(prompt)
        
        # 디버그 로깅 추가
        logging.debug(f"Raw response type: {type(response)}")
        logging.debug(f"Raw response: {response}")
        
        # response 객체 자체를 포맷팅
        formatted_response = format_llm_response(response)
        logging.debug(f"Formatted response: {formatted_response}")
        
        return formatted_response
    except Exception as e:
        logging.error(f"Error in generate_response: {str(e)}")
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
            api_key=os.getenv("GEMINI_API_KEY"),
        )
        response = llm.invoke(prompt)
        return format_llm_response(response)
    except Exception as e:
        logging.error(f"Error in generate_search_summary: {str(e)}")
        return "죄송합니다. 검색 결과를 요약하는 중에 오류가 발생했습니다."

def test_llm_simple():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.7,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    try:
        prompt = "안녕! 자기소개 해줘."
        response = llm.invoke(prompt)
        print("Simple prompt response:", response)
    except Exception as e:
        import traceback
        print("Simple prompt error:", e)
        traceback.print_exc()
