from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict
import uuid
from datetime import datetime

# 임시 데이터 저장소 (실제로는 데이터베이스 사용)
users_db: Dict[str, dict] = {}
ai_friends_db: Dict[str, dict] = {}

router = APIRouter(prefix="/api/user", tags=["user"])

# Pydantic 모델들
class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

class CreateAIFriendRequest(BaseModel):
    user_id: str
    ai_name: str
    generated_image_url: str

class SelectMBTIRequest(BaseModel):
    user_id: str
    ai_friend_id: str
    user_mbti: str
    relationship_type: str

@router.post("/signup")
async def signup(request: SignupRequest):
    """사용자 회원가입"""
    try:
        # 이메일 중복 확인
        if any(user["email"] == request.email for user in users_db.values()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일입니다."
            )
        
        # 새 사용자 생성
        user_id = str(uuid.uuid4())
        users_db[user_id] = {
            "id": user_id,
            "username": request.username,
            "email": request.email,
            "password": request.password,  # 실제로는 해시 처리 필요
            "created_at": datetime.now().isoformat(),
            "mbti": None,
            "ai_friends": []
        }
        
        return JSONResponse(content={
            "success": True,
            "user_id": user_id,
            "username": request.username,
            "message": "회원가입이 완료되었습니다."
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"회원가입 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/create-ai-friend")
async def create_ai_friend(request: CreateAIFriendRequest):
    """AI 친구 생성"""
    try:
        # 사용자 확인
        if request.user_id not in users_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        # AI 친구 생성
        ai_friend_id = str(uuid.uuid4())
        ai_friends_db[ai_friend_id] = {
            "id": ai_friend_id,
            "user_id": request.user_id,
            "name": request.ai_name,
            "image_url": request.generated_image_url,
            "mbti": None,  # 아직 결정되지 않음
            "relationship_type": None,
            "created_at": datetime.now().isoformat()
        }
        
        # 사용자의 AI 친구 목록에 추가
        users_db[request.user_id]["ai_friends"].append(ai_friend_id)
        
        return JSONResponse(content={
            "success": True,
            "ai_friend_id": ai_friend_id,
            "ai_name": request.ai_name,
            "message": "AI 친구가 성공적으로 생성되었습니다."
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 친구 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/select-mbti")
async def select_mbti(request: SelectMBTIRequest):
    """사용자 MBTI 및 관계 유형 설정"""
    try:
        # 사용자 확인
        if request.user_id not in users_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        # AI 친구 확인
        if request.ai_friend_id not in ai_friends_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI 친구를 찾을 수 없습니다."
            )
        
        # 사용자 MBTI 업데이트
        users_db[request.user_id]["mbti"] = request.user_mbti
        
        # AI 친구의 관계 유형 업데이트
        ai_friends_db[request.ai_friend_id]["relationship_type"] = request.relationship_type
        
        # AI의 MBTI는 chat.py에서 결정되므로 여기서는 설정하지 않음
        
        return JSONResponse(content={
            "success": True,
            "user_mbti": request.user_mbti,
            "relationship_type": request.relationship_type,
            "message": "MBTI와 관계 유형이 성공적으로 설정되었습니다."
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MBTI 설정 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/profile/{user_id}")
async def get_user_profile(user_id: str):
    """사용자 프로필 조회"""
    try:
        if user_id not in users_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        user = users_db[user_id].copy()
        # 비밀번호 제거
        user.pop("password", None)
        
        # AI 친구 정보 포함
        ai_friends = []
        for friend_id in user.get("ai_friends", []):
            if friend_id in ai_friends_db:
                ai_friends.append(ai_friends_db[friend_id])
        
        return JSONResponse(content={
            "success": True,
            "user": user,
            "ai_friends": ai_friends
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"프로필 조회 중 오류가 발생했습니다: {str(e)}"
        )