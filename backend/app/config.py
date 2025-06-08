# backend/app/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv() # .env 파일 불러오기

class Settings(BaseSettings):
    # 공통 MiniMax 자격 증명
    minimax_group_id: str = os.getenv("MINIMAX_GROUP_ID", "default_group_id") # WebSocket URL에서 직접 사용하지 않더라도, 다른 API 호출이나 계정 식별에 사용될 수 있음
    minimax_api_key: str = os.getenv("MINIMAX_API_KEY", "default_api_key")

    # --- 추가: MiniMax WebSocket 실시간 API 설정 ---
    minimax_ws_realtime_base_url: str = "wss://api.minimax.chat/ws/v1/realtime"
    # 기본 모델, .env 파일에서 덮어쓸 수 있음
    minimax_ws_default_model: str = os.getenv("MINIMAX_WS_DEFAULT_MODEL", "abab6.5s-chat")
    
    # 새로운 Pydantic v2 설정 방식 사용
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"  # 추가 환경 변수 무시
    }

settings = Settings()

#검증 (선택 사항)
print(f"불러온 Group ID: {settings.minimax_group_id}")
print(f"불러온 API Key: {settings.minimax_api_key}")
print(f"WebSocket Base URL: {settings.minimax_ws_realtime_base_url}")
print(f"WebSocket 기본 모델: {settings.minimax_ws_default_model}")

