from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import base64
import io
from PIL import Image
import numpy as np
import cv2

from app.emotion.analyzer import analyze_image, analysis_queue

router = APIRouter(prefix="/api/emotion", tags=["emotion"])

@router.post("/capture")
async def capture_image(request: Request):
    try:
        # 요청 본문에서 이미지 데이터 가져오기
        data = await request.json()
        image_data = data.get("image", "")
        
        # base64 디코딩
        if image_data.startswith("data:image"):
            # data:image/jpeg;base64, 같은 접두사 제거
            image_data = image_data.split(",")[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # 이미지 분석 처리
        face_emotion = analyze_image(image)
        
        # 응답 반환
        return JSONResponse(content={
            "success": True,
            "emotion": face_emotion
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
