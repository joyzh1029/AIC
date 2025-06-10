#!/usr/bin/env python3
"""최소한의 FastMCP 서버 테스트"""

import logging
from mcp.server.fastmcp import FastMCP

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 최소한의 FastMCP 서버
mcp = FastMCP("test-server")

@mcp.tool()
def hello_world(name: str = "World") -> str:
    """간단한 인사 도구"""
    result = f"Hello, {name}!"
    logger.info(f"hello_world 호출됨: {result}")
    return result

@mcp.tool()
def test_connection() -> str:
    """연결 테스트 도구"""
    result = "FastMCP 서버가 정상적으로 작동합니다!"
    logger.info(f"test_connection 호출됨: {result}")
    return result

if __name__ == "__main__":
    print("🚀 최소 FastMCP 서버 시작")
    print("📡 포트: 8000")
    print("🔗 엔드포인트: http://localhost:8000/mcp")
    
    try:
        # streamable-http로 서버 시작
        mcp.run(transport="streamable-http")
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")
        import traceback
        traceback.print_exc() 