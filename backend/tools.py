from tavily import TavilyClient
from typing import Dict, List
from backend.config import config

class SearchTool:
    """Tavily 검색 도구"""
    
    def __init__(self):
        self.tavily = TavilyClient(api_key=config.TAVILY_API_KEY)
    
    def search_web(self, query: str, count: int = 3) -> List[Dict]:
        """웹 검색"""
        try:
            print(f"🔍 Tavily 검색: {query}")
            
            # Tavily 검색 실행
            response = self.tavily.search(
                query=query,
                search_depth="basic",  # "basic" 또는 "advanced"
                max_results=count,
                include_domains=None,
                exclude_domains=None
            )
            
            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "url": item.get("url", ""),
                    "score": item.get("score", 0)
                })
            
            print(f"✅ 검색 결과: {len(results)}개")
            return results
            
        except Exception as e:
            print(f"❌ Tavily 검색 오류: {e}")
            return []
    
    def search_news(self, query: str, count: int = 3) -> List[Dict]:
        """뉴스 검색 (웹 검색과 동일하지만 뉴스 관련 키워드 추가)"""
        news_query = f"{query} 뉴스 최신"
        return self.search_web(news_query, count)
    
    def get_answer(self, query: str) -> str:
        """Tavily의 답변 생성 기능 사용"""
        try:
            print(f"🤖 Tavily 답변 생성: {query}")
            
            response = self.tavily.qna_search(query=query)
            answer = response.get("answer", "")
            
            print(f"✅ 답변 생성 완료")
            return answer
            
        except Exception as e:
            print(f"❌ Tavily 답변 생성 오류: {e}")
            return ""