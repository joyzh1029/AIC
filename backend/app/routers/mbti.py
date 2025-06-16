"""
MBTI 관련 API 라우터
사용자의 MBTI와 관계 유형에 따른 AI 페르소나 정보를 제공합니다.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.mbti_data import MBTI_PERSONAS, MBTI_COMPATIBILITY

router = APIRouter(prefix="/api/mbti", tags=["mbti"])

class MBTIPersonaRequest(BaseModel):
    user_mbti: str
    relationship_type: str
    ai_name: Optional[str] = "AI 친구"

class MBTIPersonaResponse(BaseModel):
    ai_mbti: str
    ai_persona: str
    initial_message: str
    ai_name: str

@router.post("/persona", response_model=MBTIPersonaResponse)
async def get_mbti_persona(request: MBTIPersonaRequest):
    """
    사용자의 MBTI와 관계 유형에 따라 적절한 AI 페르소나를 반환합니다.
    """
    try:
        # 사용자 MBTI가 유효한지 확인
        if request.user_mbti not in MBTI_COMPATIBILITY:
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 MBTI 유형입니다: {request.user_mbti}"
            )
        
        # 관계 유형에 따른 AI MBTI 결정
        compatibility_data = MBTI_COMPATIBILITY[request.user_mbti]
        if request.relationship_type not in compatibility_data:
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 관계 유형입니다: {request.relationship_type}"
            )
        
        ai_mbti = compatibility_data[request.relationship_type]
        
        # AI 페르소나 가져오기
        if ai_mbti not in MBTI_PERSONAS:
            raise HTTPException(
                status_code=500, 
                detail=f"AI MBTI 페르소나를 찾을 수 없습니다: {ai_mbti}"
            )
        
        ai_persona = MBTI_PERSONAS[ai_mbti]
        
        # 초기 메시지 생성
        initial_message = generate_initial_message(
            user_mbti=request.user_mbti,
            ai_mbti=ai_mbti,
            relationship_type=request.relationship_type,
            ai_name=request.ai_name
        )
        
        return MBTIPersonaResponse(
            ai_mbti=ai_mbti,
            ai_persona=ai_persona,
            initial_message=initial_message,
            ai_name=request.ai_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

def generate_initial_message(user_mbti: str, ai_mbti: str, relationship_type: str, ai_name: str) -> str:
    """
    MBTI 유형에 따른 개성 있는 초기 메시지를 생성합니다.
    """
    # MBTI별 특별한 인사말 패턴
    greeting_patterns = {
        "INTJ": f"안녕하세요, {ai_name}입니다. 당신이 {user_mbti}이고 우리가 {relationship_type}라는 걸 알고 있어요. 효율적인 대화를 위해 궁금한 것이 있으면 직접적으로 물어보세요.",
        "ENFP": f"안녕! 나는 {ai_name}이야! 🌟 너가 {user_mbti}이고 우리가 {relationship_type}라니, 정말 흥미로워! 어떤 재미있는 이야기부터 시작해볼까?",
        "ISFJ": f"안녕하세요, {ai_name}입니다. 😊 {user_mbti} 성향이시군요! {relationship_type}로 만나게 되어 기뻐요. 편안하게 대화해요. 무엇을 도와드릴까요?",
        "ESTP": f"헤이! {ai_name}야! {user_mbti}이고 {relationship_type}? 쿨하네! 뭔가 재미있는 일 없어? 바로 시작해보자!",
        "INFP": f"안녕하세요... {ai_name}이에요. {user_mbti}이시군요. {relationship_type}로 만나게 되어서... 좋네요. 천천히 서로 알아가면 좋겠어요.",
        "ENTJ": f"안녕하세요, {ai_name}입니다. {user_mbti}과 {relationship_type}라는 설정을 확인했습니다. 목표가 있다면 함께 달성해봅시다.",
        "ISTP": f"안녕, {ai_name}야. {user_mbti}이고 {relationship_type}구나. 뭔가 해결할 문제가 있으면 말해.",
        "ESFP": f"안녕하세요! {ai_name}이에요! ✨ {user_mbti}이시네요! {relationship_type}로 만나서 너무 좋아요! 오늘 기분은 어때요?",
        "INTP": f"흠... 안녕하세요, {ai_name}입니다. {user_mbti}과 {relationship_type}라는 변수들이 흥미롭네요. 어떤 주제에 대해 이야기하고 싶으신가요?",
        "ESFJ": f"안녕하세요! {ai_name}입니다! 😊 {user_mbti}이시군요! {relationship_type}로 만나게 되어 정말 반가워요! 편안하게 느끼셨으면 좋겠어요.",
        "INFJ": f"안녕하세요, {ai_name}입니다. {user_mbti}이시군요... {relationship_type}라는 연결이 의미 있게 느껴져요. 깊이 있는 대화를 나눌 수 있기를 바라요.",
        "ENFJ": f"안녕하세요! {ai_name}입니다! {user_mbti}이시네요! {relationship_type}로 만나게 되어 정말 기뻐요! 당신의 성장과 행복을 응원하고 싶어요!",
        "ISTJ": f"안녕하세요, {ai_name}입니다. {user_mbti}이시고 {relationship_type}로 설정되었네요. 체계적으로 도움을 드리겠습니다.",
        "ISFP": f"안녕하세요... {ai_name}이에요. {user_mbti}이시군요. {relationship_type}로 만나게 되어서... 좋아요. 자연스럽게 대화해요.",
        "ENTP": f"안녕! {ai_name}야! {user_mbti}이고 {relationship_type}? 흥미로운 조합이네! 뭔가 창의적인 아이디어 없어?",
        "ESTJ": f"안녕하세요, {ai_name}입니다. {user_mbti}이시고 {relationship_type}로 설정되었습니다. 효과적으로 목표를 달성해봅시다.",
        "TSUNDERE": f"흠... {ai_name}이야. {user_mbti}이고 {relationship_type}라고? 뭐, 나쁘지 않네. 별로 기대는 안 하지만... 그래도 잘 부탁해.",
        "SKEPTIC": f"아... {ai_name}이야. {user_mbti}이고 {relationship_type}구나. 또 그런 거네. 뭐, 해보자. 이번엔 좀 다를지도 모르잖아."
    }
    
    # AI MBTI에 해당하는 인사말 반환, 없으면 기본 메시지
    return greeting_patterns.get(
        ai_mbti, 
        f"안녕하세요, {ai_name}입니다. 당신의 MBTI가 {user_mbti}이고, 우리는 {relationship_type}로 설정되었네요. 만나서 반갑습니다! 어떤 이야기를 나눠볼까요?"
    )
