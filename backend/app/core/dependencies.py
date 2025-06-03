"""
API 라우트 의존성 모듈
이 모듈은 API 라우트가 사용하는 다양한 의존성 함수를 제공합니다
"""
from fastapi import Depends, HTTPException, status, Request, Header
from typing import Optional, List, Dict, Any
import time
from fastapi.security import OAuth2PasswordBearer
import logging

# 로그 설정
logger = logging.getLogger(__name__)

# 선택적 OAuth2 인증(프로젝트가 필요한 경우)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# 요청 시간 측정 미들웨어
async def measure_execution_time(request: Request, call_next):
    """API 요청 실행 시간 측정 미들웨어"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Request to {request.url.path} took {process_time:.4f} seconds")
    return response

# API 버전 의존성
async def get_api_version(
    x_api_version: Optional[str] = Header(None, description="API 버전")
) -> str:
    """API 버전 의존성"""
    if x_api_version is None:
        return "v1"  # 기본 버전
    return x_api_version

# 선택적 사용자 인증 의존성
async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[Dict[str, Any]]:
    """
    사용자 인증 의존성 (테스트를 위해 임시 비활성화)
    테스트를 위해 항상 테스트 사용자를 반환합니다
    """
    # 테스트를 위해 Firebase 인증 비활성화
    # 항상 테스트 사용자 반환
    logger.info("Firebase authentication disabled for testing. Using test user.")
    user = {"id": "test123", "username": "testuser"}
    return user

# 필수 사용자 인증 의존성
async def get_current_active_user(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    사용자 인증 의존성
    사용자가 인증되어야 함
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증필요",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

# 일반 오류 처리
def handle_exceptions(request: Request, exc: Exception) -> Dict[str, Any]:
    """일반 오류 처리 함수"""
    logger.error(f"Error processing request {request.url.path}: {str(exc)}")
    
    if isinstance(exc, HTTPException):
        return {
            "success": False,
            "error": {
                "code": exc.status_code,
                "message": exc.detail
            }
        }
    
    # 다른 유형의 예외 처리
    return {
        "success": False,
        "error": {
            "code": 500,
            "message": "서버내부오류"
        }
    }
