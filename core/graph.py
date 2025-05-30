# LangGraph 기반 뉴스 요약 파이프라인

from langgraph.graph import StateGraph, END
from typing import TypedDict, Any

class NewsState(TypedDict):
    query: str
    category: str
    articles: list
    docs: list
    retriever: Any
    relevant_docs: list
    answer: str

def create_graph():
    g = StateGraph(NewsState)
    
    # Node 함수들을 람다로 정의
    nodes = {
        "detect": lambda s: {**s, "category": detect_category(s["query"])},
        "fetch": lambda s: {**s, "articles": load_cache() or fetch_news()},
        "format": lambda s: {**s, "docs": to_docs(s["articles"])},
        "vector": lambda s: {**s, "retriever": build_vectorstore(s["docs"]).as_retriever()},
        "retrieve": lambda s: {**s, "relevant_docs": s["retriever"].invoke(s["query"])},
        "summarize": lambda s: {**s, "answer": ask_gemini(
            f"다음 뉴스 내용을 요약해줘:\n" + 
            "\n\n".join([d.page_content for d in s["relevant_docs"][:3]])
        )}
    }
    
    # 노드 추가 및 엣지 연결
    for name, func in nodes.items():
        g.add_node(name, func)
    
    edges = [("detect", "fetch"), ("fetch", "format"), ("format", "vector"),
             ("vector", "retrieve"), ("retrieve", "summarize"), ("summarize", END)]
    
    g.set_entry_point("detect")
    for start, end in edges:
        g.add_edge(start, end)
    
    return g.compile()

app = create_graph()