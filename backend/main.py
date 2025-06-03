import os
import sys
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가 (상대 경로 임포트를 위함)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 导入集中式路由管理模块
from app.routers import api_router

# 코어 모듈 임포트
from app.core.startup import initialize_models, start_background_threads, initialize_directories, shutdown_threads

# FastAPI 앱 초기화
app = FastAPI(
    title="AIC API",
    description="AI Companion Backend API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 디렉토리 초기화
BASE_DIR = initialize_directories()

# 정적 파일 서비스 설정 (업로드된 파일과 생성된 아바타 접근용)
app.mount("/uploads", StaticFiles(directory=str(BASE_DIR / "uploads")), name="uploads")

# 注册所有路由（一次性注册）
app.include_router(api_router)

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "서버가 정상적으로 실행 중입니다."}

# FastAPI 앱 실행 (uvicorn에서 실행할 때 사용)
@app.on_event("startup")
async def startup_event():
    # 모델 로딩
    global processor, vlm_model, device, whisper_model
    processor, vlm_model, device, whisper_model = initialize_models()
    
    # 분석 스레드 시작
    global webcam, analyzer
    webcam, analyzer = start_background_threads(vlm_model, processor, device, whisper_model)

@app.on_event("shutdown")
async def shutdown_event():
    # 스레드 종료 이벤트 설정
    shutdown_threads()

if __name__ == "__main__":
    import uvicorn
    
    # FastAPI 앱 실행
    print("🚀 서버 시작 - http://localhost:8181")
    uvicorn.run(app, host="0.0.0.0", port=8181)
