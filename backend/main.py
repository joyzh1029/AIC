from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 라우터 임포트
from app.routers.avatar import router as avatar_router
from app.routers.camera_util import router as camera_router, camera_state
from app.routers.camera import router as camera_simple_router
from app.routers.chat import router as chat_router
from app.routers.comfyui import router as image_router
from app.routers.emotion import router as emotion_router
from app.routers.health_check import router as health_router
from app.routers.save_chat import router as save_chat_router
from app.routers.user import router as user_router, api_router as user_api_router
from app.routers.tts import router as tts_router
from app.routers.websocket_rt import router as websocket_router

app = FastAPI()

# 강화된 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "http://localhost:3000",
        # "http://127.0.0.1:3000",
        # "http://localhost:5173",  # Vite 기본 포트
        # "http://127.0.0.1:5173",
        # "http://localhost:3001",
        # "http://127.0.0.1:3001",
        "http://localhost:8080",  # 프론트엔드 실행 포트
        "http://127.0.0.1:8080",
        "*",  # 개발용 - 모든 origin 허용
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 라우터 등록
app.include_router(websocket_router)
app.include_router(image_router)  # ComfyUI: /wanna-image/ 경로
app.include_router(chat_router)
app.include_router(save_chat_router)
app.include_router(user_router)  # 기존 경로 (/get_user_data)
app.include_router(user_api_router)  # API 경로 (/api/get_user_data)
app.include_router(camera_router)
app.include_router(tts_router)
app.include_router(health_router)
app.include_router(avatar_router)
app.include_router(camera_simple_router)
app.include_router(emotion_router)


# 디버깅용 미들웨어
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"🔍 요청: {request.method} {request.url}")
    response = await call_next(request)
    print(f"🔍 응답: {response.status_code}")
    return response


@app.on_event("shutdown")
def shutdown_event():
    # 서버 종료 시 카메라 해제
    with camera_state.lock:
        if camera_state.camera is not None:
            camera_state.camera.release()
            camera_state.camera = None
        camera_state.is_running = False


if __name__ == "__main__":
    print("통합 AI 서버 작동중... (포트 8181)")
    print("CORS: 모든 origin 허용됨")
    print("모든 요청/응답이 로깅됩니다")
    uvicorn.run("main:app", host="0.0.0.0", port=8181, reload=True)
