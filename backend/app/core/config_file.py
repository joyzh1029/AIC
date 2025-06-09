# app/core/config.py
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class Settings(BaseSettings):
    """
    애플리케이션 설정
    """
    # API 설정
    app_name: str = "AI 채팅 및 일정 관리"
    app_version: str = "1.0.0"
    api_prefix: str = "/api"
    
    # Google AI 설정
    google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
    google_model: str = "gemini-pro"
    
    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8181
    reload: bool = True
    
    # CORS 설정
    cors_origins: list = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    # 일정 관리 설정
    schedule_default_reminder_minutes: int = 30
    schedule_max_query_days: int = 30
    
    # WebSocket 설정
    ws_heartbeat_interval: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 전역 설정 인스턴스 생성
settings = Settings()

# 필요한 설정 검증
def validate_settings():
    """필요한 설정이 있는지 검증"""
    errors = []
    
    if not settings.google_api_key:
        errors.append("GOOGLE_API_KEY가 설정되지 않았습니다")
    
    if errors:
        print("⚠️  설정 오류:")
        for error in errors:
            print(f"   - {error}")
        print("\n.env 파일에 필요한 환경 변수를 설정해주세요")
        return False
    
    return True