from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import os
import uuid
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from app.avatar.generator import extract_features, generate_avatar
from app.core.dependencies import get_api_version, get_current_user

# 업로드 디렉토리 설정
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ORIGINAL_DIR = BASE_DIR / "uploads" / "original"
GENERATED_DIR = BASE_DIR / "uploads" / "generated"

# 디렉토리 생성
os.makedirs(ORIGINAL_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)

# 로그 설정
logger = logging.getLogger(__name__)

# 라우터 생성, 태그와 설명 추가
router = APIRouter(
    prefix="/api/avatar",
    tags=["avatar"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "리소스를 찾을 수 없음"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "서버 내부 오류"}
    }
)

@router.post("/upload", 
          summary="사용자 사진 업로드",
          description="사용자 사진을 업로드하고 서버에 저장",
          response_description="업로드 성공 시 파일 경로 반환")
async def upload_photo(
    file: UploadFile = File(...), 
    user_id: str = Form(...),
    api_version: str = Depends(get_api_version),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """사용자 사진 업로드 및 저장"""
    try:
        # API 버전과 사용자 정보 기록
        logger.info(f"Upload photo API called with version {api_version}")
        if current_user:
            logger.info(f"Authenticated user: {current_user.get('username')}")
        
        # 파일 확장자 검증
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in [".jpg", ".jpeg", ".png"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="JPG, JPEG 또는 PNG 파일만 업로드 가능합니다"
            )
        
        # 고유한 파일 이름 생성
        unique_filename = f"{user_id}_{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(ORIGINAL_DIR, unique_filename)
        
        # 파일 저장
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"Successfully uploaded file: {unique_filename}")
        return JSONResponse({
            "success": True,
            "message": "사진 업로드 성공",
            "file_path": unique_filename,
            "api_version": api_version
        })
    except HTTPException as he:
        # HTTP 예외를 직접 다시 발생시킴
        logger.error(f"HTTP error during upload: {he.detail}")
        raise
    except Exception as e:
        # 자세한 오류를 기록하고 일반적인 오류 메시지 반환
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"업로드 실패: {str(e)}"
        )

@router.post("/generate",
          summary="사용자 아바타 생성",
          description="업로드한 사진을 기반으로 AI 아바타 생성",
          response_description="생성 성공 시 아바타 URL 반환")
async def create_avatar(
    file_path: str = Form(...), 
    user_id: str = Form(...),
    api_version: str = Depends(get_api_version),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """업로드된 사진으로 아바타 생성"""
    try:
        # 원본 파일 경로
        original_path = os.path.join(ORIGINAL_DIR, file_path)
        if not os.path.exists(original_path):
            raise HTTPException(status_code=404, detail="업로드된 파일을 찾을 수 없습니다.")
        
        # 출력 파일 경로
        output_filename = f"{user_id}_avatar_{uuid.uuid4()}.png"
        output_path = os.path.join(GENERATED_DIR, output_filename)
        
        # 특징 추출
        features = extract_features(original_path)
        
        # 아바타 생성
        generate_avatar(features, output_path)
        
        # 상대 URL 경로 생성 (프론트엔드에서 접근 가능한)
        relative_path = f"/uploads/generated/{output_filename}"
        
        return JSONResponse({
            "success": True,
            "message": "아바타가 성공적으로 생성되었습니다.",
            "avatar_path": relative_path
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"아바타 생성 실패: {str(e)}")
