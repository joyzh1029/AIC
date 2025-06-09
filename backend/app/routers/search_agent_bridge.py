import aiohttp
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter()

class SearchRequest(BaseModel):
    user_id: str
    text: str
    search_type: str = "web"

class SearchResult(BaseModel):
    title: str
    snippet: str
    link: Optional[str] = None
    description: Optional[str] = None

@router.post("/api/search/chat")
async def search_chat(request: SearchRequest):
    """
    Google 검색 Agent와 연결하는 API 엔드포인트
    프론트엔드에서 검색 요청을 받아 localhost:8000의 검색 엔진으로 전달
    """
    try:
        logger.info(f"Search request received: {request.text} for user: {request.user_id}")
        
        # Timeout 설정
        timeout = aiohttp.ClientTimeout(total=30)
        
        # Google Search Agent API 호출
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(
                    "http://127.0.0.1:8000/search",  # Google Search Agent 엔드포인트
                    json={
                        "query": request.text,
                        "search_type": request.search_type,
                        "user_id": request.user_id
                    },
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        search_results = await response.json()
                        logger.info(f"Search results received: {len(search_results.get('results', []))} items")
                        
                        # 검색 결과 포맷팅
                        formatted_results = format_search_results(search_results)
                        
                        return {
                            "success": True,
                            "results": search_results.get("results", []),
                            "message": {
                                "text": formatted_results
                            },
                            "search_type": request.search_type,
                            "query": request.text
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Search agent error: {response.status} - {error_text}")
                        raise HTTPException(
                            status_code=response.status, 
                            detail=f"Search agent returned error: {error_text}"
                        )
                        
            except aiohttp.ClientError as e:
                logger.error(f"Connection error to search agent: {str(e)}")
                raise HTTPException(
                    status_code=503, 
                    detail="검색 서비스에 연결할 수 없습니다."
                )
            except asyncio.TimeoutError:
                logger.error("Search request timeout")
                raise HTTPException(
                    status_code=504, 
                    detail="검색 요청 시간이 초과되었습니다."
                )
                    
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        logger.error(f"Unexpected error in search_chat: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": {
                "text": "검색 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }
        }

def format_search_results(results: Dict[str, Any]) -> str:
    """
    검색 결과를 사용자 친화적인 형태로 포맷팅
    """
    if not results or not results.get("results"):
        return "🔍 검색 결과를 찾을 수 없습니다."
    
    search_results = results["results"]
    query = results.get("query", "")
    
    formatted = f"🔍 '{query}' 검색 결과:\n\n"
    
    # 최대 5개 결과만 표시
    for idx, result in enumerate(search_results[:5], 1):
        title = result.get('title', '제목 없음')
        snippet = result.get('snippet', result.get('description', ''))
        link = result.get('link', result.get('url', ''))
        
        formatted += f"**{idx}. {title}**\n"
        
        if snippet:
            # 스니펫이 너무 길면 자르기
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."
            formatted += f"{snippet}\n"
        
        if link:
            formatted += f"🔗 [자세히 보기]({link})\n"
        
        formatted += "\n"
    
    # 총 결과 수 표시
    total_results = len(search_results)
    if total_results > 5:
        formatted += f"💡 총 {total_results}개의 검색 결과 중 상위 5개를 표시했습니다.\n"
    
    return formatted

@router.get("/api/search/health")
async def search_health():
    """
    검색 Agent 연결 상태 확인
    """
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get("http://127.0.0.1:8000/health") as response:
                if response.status == 200:
                    return {
                        "status": "healthy",
                        "search_agent": "connected",
                        "message": "Google 검색 Agent가 정상적으로 연결되어 있습니다."
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "search_agent": "error",
                        "message": f"검색 Agent 응답 오류: {response.status}"
                    }
    except Exception as e:
        return {
            "status": "unhealthy",
            "search_agent": "disconnected",
            "message": f"검색 Agent에 연결할 수 없습니다: {str(e)}"
        }

@router.post("/api/search/suggest")
async def search_suggest(request: SearchRequest):
    """
    검색 제안 기능 (선택사항)
    """
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "http://127.0.0.1:8000/suggest",
                json={
                    "query": request.text,
                    "user_id": request.user_id
                }
            ) as response:
                if response.status == 200:
                    suggestions = await response.json()
                    return {
                        "success": True,
                        "suggestions": suggestions.get("suggestions", []),
                        "query": request.text
                    }
                else:
                    return {
                        "success": False,
                        "suggestions": [],
                        "message": "검색 제안을 가져올 수 없습니다."
                    }
    except Exception as e:
        logger.error(f"Search suggestion error: {str(e)}")
        return {
            "success": False,
            "suggestions": [],
            "message": "검색 제안 서비스에 오류가 발생했습니다."
        } 