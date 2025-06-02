import os
from typing import Dict

from dotenv import load_dotenv

load_dotenv()

class Config:
    """API 키 및 설정 관리"""
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY", "")
    NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
    NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
    
    # Vector DB 설정
    EMBEDDING_MODEL = "text-embedding-3-small"
    VECTOR_DB_PATH = "./vector_store"
    
    # Agent 설정
    LLM_MODEL = "gpt-3.5-turbo"
    MAX_SEARCH_RESULTS = 5
    
    @classmethod
    def validate(cls) -> bool:
        """필수 API 키 검증"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        if not cls.TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY가 설정되지 않았습니다.")
        return True
    
    @classmethod
    def get_headers(cls, service: str) -> Dict[str, str]:
        """서비스별 API 헤더 반환"""
        headers = {
            "kakao": {
                "Authorization": f"KakaoAK {cls.KAKAO_REST_API_KEY}"
            },
            "naver": {
                "X-Naver-Client-Id": cls.NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": cls.NAVER_CLIENT_SECRET
            }
        }
        return headers.get(service, {})

# Config 인스턴스 생성
config = Config()