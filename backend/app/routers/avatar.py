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

# 设置日志
logger = logging.getLogger(__name__)

# 创建路由器，添加标签和描述
router = APIRouter(
    prefix="/api/avatar",
    tags=["avatar"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "未找到资源"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "服务器内部错误"}
    }
)

@router.post("/upload", 
          summary="上传用户照片",
          description="上传用户照片并保存到服务器",
          response_description="上传成功返回文件路径")
async def upload_photo(
    file: UploadFile = File(...), 
    user_id: str = Form(...),
    api_version: str = Depends(get_api_version),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """사용자 사진 업로드 및 저장"""
    try:
        # 记录API版本和用户信息
        logger.info(f"Upload photo API called with version {api_version}")
        if current_user:
            logger.info(f"Authenticated user: {current_user.get('username')}")
        
        # 文件扩展名验证
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in [".jpg", ".jpeg", ".png"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="只能上传JPG、JPEG或PNG文件"
            )
        
        # 创建唯一文件名
        unique_filename = f"{user_id}_{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(ORIGINAL_DIR, unique_filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"Successfully uploaded file: {unique_filename}")
        return JSONResponse({
            "success": True,
            "message": "照片上传成功",
            "file_path": unique_filename,
            "api_version": api_version
        })
    except HTTPException as he:
        # 直接重新抛出HTTP异常
        logger.error(f"HTTP error during upload: {he.detail}")
        raise
    except Exception as e:
        # 记录详细错误并返回通用错误消息
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"上传失败: {str(e)}"
        )

@router.post("/generate",
          summary="生成用户头像",
          description="根据上传的照片生成AI头像",
          response_description="生成成功返回头像URL")
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
