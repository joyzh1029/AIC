import cv2
import base64
import io
import numpy as np
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import uvicorn

# 얼굴 감정 분석 함수 (간단한 구현)
def analyze_facial_expression(image):
    # 실제 분석 로직이 없으므로 기본값 반환
    return "neutral"

# FastAPI 앱 초기화
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 카메라 캡처 API 엔드포인트
@app.post("/api/camera/capture")
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
        
        # 이미지 분석 처리 (간단한 구현)
        face_emotion = analyze_facial_expression(image)
        
        # 응답 반환
        return JSONResponse(content={
            "success": True,
            "emotion": face_emotion,
            "message": "이미지가 성공적으로 분석되었습니다."
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"이미지 처리 중 오류 발생: {str(e)}"})

# 루트 경로
@app.get("/")
def root():
    return {"message": "카메라 서버가 실행 중입니다"}

# 상태 확인 엔드포인트
@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("카메라 서버 시작 중...")
    uvicorn.run(app, host="0.0.0.0", port=8181)
