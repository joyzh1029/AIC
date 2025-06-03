import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 현재 디렉토리를 Python 경로에 추가 (상대 경로 임포트를 위함)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# 중앙 집중식 라우팅 관리 모듈 가져오기
from app.routers import api_router

# 코어 모듈 임포트
from app.core.startup import initialize_models, start_background_threads, initialize_directories, shutdown_threads

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 작업
    print("AI Companion API 서버 시작 중...")
    
    # 모델 로딩
    global processor, vlm_model, device, whisper_model
    processor, vlm_model, device, whisper_model = initialize_models()
    
    # 분석 스레드 시작
    global analyzer
    analyzer = start_background_threads(vlm_model, processor, device, whisper_model)
    
    yield
    
    # 종료 시 작업
    print("서버 종료 중...")
    # 스레드 종료 이벤트 설정
    shutdown_threads()

# FastAPI 앱 초기화
app = FastAPI(
    title="AIC API",
    description="AI Companion Backend API with Schedule Management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인 설정 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 디렉토리 초기화
BASE_DIR = initialize_directories()

# 정적 파일 서비스 설정 (업로드된 파일과 생성된 아바타 접근용)
app.mount("/uploads", StaticFiles(directory=str(BASE_DIR / "uploads")), name="uploads")

# 모든 라우트 등록 (일괄 등록)
app.include_router(api_router)

# 루트 경로 및 헬스체크 엔드포인트
@app.get("/")
async def root():
    return {
        "message": "AIC API 서버에 오신 것을 환영합니다",
        "documentation": "/docs",
        "health_check": "/health",
        "version": "1.0.0",
        "endpoints": [
            "/api/chat",
            "/api/schedule/chat",
            "/api/schedule/events",
            "/api/schedule/tts",
            "/api/avatar",
            "/api/camera",
            "/api/emotion"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-companion",
        "environment": {
            "google_api_key": "configured" if os.getenv("GOOGLE_API_KEY") else "missing"
        },
        "message": "서버가 정상적으로 실행 중입니다."
    }

# 이전 이벤트 핸들러는 lifespan 컨텍스트 매니저로 대체되었습니다

if __name__ == "__main__":
    import uvicorn
    
    # 필요한 환경 변수 확인
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  경고: GOOGLE_API_KEY가 설정되지 않았습니다!")
        print(".env 파일에 설정하세요: GOOGLE_API_KEY=your_key_here")
    
    # FastAPI 앱 실행
    print("🚀 서버 시작 - http://localhost:8181")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8181,
        reload=True
    )
