import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
import asyncio

# 현재 디렉토리를 Python 경로에 추가 (상대 경로 임포트를 위함)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# 중앙 집중식 라우팅 관리 모듈 가져오기
from app.routers import api_router
# 모델 관련 함수들 임포트
from app.models.models import initialize_models, shutdown_threads

app = FastAPI()
app.include_router(api_router)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def initialize_directories() -> Path:
    """
    필요한 디렉토리들을 생성하고 기본 경로를 반환하는 함수
    """
    # 프로젝트 루트 디렉토리
    base_dir = Path(__file__).resolve().parent

    # 필요한 디렉토리들 생성
    directories = [
        base_dir / "uploads",          # 업로드된 파일 저장
        base_dir / "uploads" / "avatars",  # 아바타 이미지 저장
        base_dir / "uploads" / "audio",    # 오디오 파일 저장
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    return base_dir

# 디렉토리 초기화
BASE_DIR = initialize_directories()

# 정적 파일 서비스 설정 (업로드된 파일과 생성된 아바타 접근용)
app.mount("/uploads", StaticFiles(directory=str(BASE_DIR / "uploads")), name="uploads")

# 루트 경로 및 헬스체크 엔드포인트
@app.get("/")
async def root():
    return {
        "message": "AIC API 서버에 오신 것을 환영합니다",
        "documentation": "/docs",
        "health_check": "/health",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "서버가 정상적으로 실행 중입니다."}

# FastAPI 앱 실행 (uvicorn에서 실행할 때 사용)
@app.on_event("startup")
async def startup_event():
    print("🔧 모델 로딩 중...")
    
    # 비동기 모델 로딩 함수
    async def load_models_async():
        global processor, vlm_model, device, whisper_model
        try:
            processor, vlm_model, device, whisper_model = await asyncio.to_thread(initialize_models)
            print("✅ 모델 로딩 완료")
        except Exception as e:
            print(f"❌ 모델 로딩 실패: {str(e)}")
            raise
    
    # 백그라운드 태스크로 실행
    asyncio.create_task(load_models_async())

@app.on_event("shutdown")
async def shutdown_event():
    try:
        # 스레드 종료 이벤트 설정
        shutdown_threads()
        print("✅ 서버 종료 완료")
    except Exception as e:
        print(f"❌ 서버 종료 중 오류: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    # FastAPI 앱 실행
    print("🚀 서버 시작 - http://localhost:8183")
    uvicorn.run(app, host="0.0.0.0", port=8183)
