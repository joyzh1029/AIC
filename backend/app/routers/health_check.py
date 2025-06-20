from datetime import datetime
from fastapi import APIRouter

router = APIRouter()


# ==================== 헬스 체크 ====================
@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.get("/")
def root():
    return {"message": "통합 AI 서버가 실행 중입니다"}
