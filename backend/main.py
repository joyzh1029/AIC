import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# 환경 변수 로드
load_dotenv()

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,  # Default level, change to logging.DEBUG for more verbosity
    format="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s (%(filename)s:%(lineno)d)",
    handlers=[
        logging.StreamHandler()  # Ensures logs go to the console
    ]
)
# 코어 모듈 임포트
from app.core.startup import initialize_models, start_background_threads, initialize_directories, shutdown_threads
from app.core.global_instances import set_global_analyzer, set_global_models
from app.nlp.llm import configure_gemini # Gemini API 구성 추가

# FastAPI 앱 초기화
app = FastAPI(
    title="AIC API",
    description="AI Companion Backend API",
    version="1.0.0"
)

# Create logger for this module
logger = logging.getLogger(__name__)
logger.info("Logging configured.")

# Add current directory to Python path for relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 코어 모듈 임포트
try:
    from app.core.startup import initialize_models, start_background_threads, initialize_directories, shutdown_threads
    logger.info("Core startup modules imported successfully")
except ImportError:
    logger.warning("Core startup modules not found or incomplete")
    initialize_models = start_background_threads = initialize_directories = shutdown_threads = None

# WebSocket 라우터 가져오기
try:
    # 새 버전 구조화된 라우터
    from app.websocket import websocket_router
    logger.info("WebSocket router imported successfully.")
except ImportError:
    logger.warning("WebSocket router not found")
    websocket_router = None

# API 라우터 가져오기
try:
    from app.routers import api_router
    logger.info("API router imported successfully.")
except ImportError:
    logger.warning("API router not found")
    api_router = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 작업
    logger.info("AI Companion API 서버 시작 중...")
    
    # Gemini API 구성 (가장 먼저 실행)
    try:
        configure_gemini()
        logger.info("Gemini API 구성 완료")
    except Exception as e:
        logger.error(f"Gemini API 구성 실패: {str(e)}")
        # Gemini 구성 실패해도 서버는 계속 실행
    
    if initialize_directories:
        BASE_DIR = initialize_directories()
        logger.info(f"Directories initialized at {BASE_DIR}")
    
    # 모델과 스레드 초기화
    if initialize_models and start_background_threads:
        try:
            # 모델 초기화 및 반환값 저장
            processor, vlm_model, device, whisper_model = initialize_models()
            logger.info("Models initialized successfully")
            
            # 반환받은 모델로 스레드 시작
            analyzer = start_background_threads(vlm_model, processor, device, whisper_model)
            logger.info("Background threads started")
        except Exception as e:
            logger.error(f"Error initializing models or threads: {str(e)}")
    else:
        logger.warning("Model initialization or thread starting functions not available")
    
    yield
    
    # 종료 시 작업
    logger.info("서버 종료 중...")
    if shutdown_threads:
        try:
            shutdown_threads()
            logger.info("Background threads shutdown successfully")
        except Exception as e:
            logger.error(f"Error shutting down threads: {str(e)}")

# FastAPI application
# FastAPI 애플리케이션 설정
app = FastAPI(
    title="AI Companion API",
    description="AI Companion Backend API with Schedule Management and Realtime Chat",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 설정
if initialize_directories:
    BASE_DIR = initialize_directories()
    # 정적 파일 서비스 설정 (업로드된 파일과 생성된 아바타 접근용)
    app.mount("/uploads", StaticFiles(directory=str(BASE_DIR / "uploads")), name="uploads")

# 라우터 등록
if websocket_router:
    app.include_router(websocket_router)

if api_router:
    app.include_router(api_router)

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
            "/api/emotion",
            "/api/search/chat",
            "/api/search/health",
            "/api/search/suggest"
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
    
    # Gemini API 및 모델 초기화
    configure_gemini() 

@app.on_event("shutdown")
async def shutdown_event():
    # 스레드 종료 이벤트 설정
    shutdown_threads()

# 애플리케이션 직접 실행 시
if __name__ == "__main__":
    import uvicorn
    
    # 필요한 환경 변수 확인
    if not os.getenv("GOOGLE_API_KEY"):
        print(" 경고: GOOGLE_API_KEY가 설정되지 않았습니다!")
        print(".env 파일에 설정하세요: GOOGLE_API_KEY=your_key_here")
    
    # FastAPI 앱 실행
    print(" 서버 시작 - http://localhost:8181")
    logger.info("Starting AI Companion API server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8181,
        reload=True
    )
