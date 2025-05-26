import uvicorn
import asyncio
import os
from dotenv import load_dotenv
from db.csv_database import CSVDatabase

# 환경 변수 로드
load_dotenv()
async def setup():
    """초기화 설정"""
    # 데이터 디렉토리 존재 확인
    CSVDatabase.ensure_data_dir()
    print("데이터 디렉토리가 초기화되었습니다")

if __name__ == "__main__":
    # 초기화 실행
    asyncio.run(setup())
    
    # FastAPI 애플리케이션 시작
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

