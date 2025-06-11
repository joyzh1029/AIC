import os
import sys
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가 (상대 경로 임포트를 위함)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 중앙 집중식 라우팅 관리 모듈 가져오기
from app.routers import api_router

# 코어 모듈 임포트
from app.core.startup import initialize_models, start_background_threads, initialize_directories, shutdown_threads
from app.core.global_instances import set_global_analyzer, set_global_models
from app.nlp.llm import configure_gemini # ✨ configure_gemini 임포트 추가

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

# 모든 라우트 등록 (일괄 등록)
app.include_router(api_router)

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
    # 모델 로딩
    global processor, vlm_model, device, whisper_model
    processor, vlm_model, device, whisper_model = initialize_models()
    set_global_models(vlm_model, processor, device, whisper_model)

    # 분석 스레드 시작
    global analyzer
    analyzer = start_background_threads(vlm_model, processor, device, whisper_model)
    set_global_analyzer(analyzer)
    
    # ✨ Gemini API 및 모델 초기화
    configure_gemini() # ✨ 이 줄 추가

@app.on_event("shutdown")
async def shutdown_event():
    # 스레드 종료 이벤트 설정
    shutdown_threads()

if __name__ == "__main__":
    import uvicorn
    
    # FastAPI 앱 실행
    print("🚀 서버 시작 - http://localhost:8181")
    uvicorn.run(app, host="0.0.0.0", port=8181)
