from langgraph.graph import StateGraph, END
from typing import TypedDict, Any
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

class NewsState(TypedDict):
    query: str
    category: str
    articles: list
    docs: list
    retriever: Any
    relevant_docs: list
    answer: str

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def to_docs(articles):
    return [
        Document(
            page_content=f"{a.get('title', '')}\n\n{a.get('description', '')}\n\n{a.get('content', '')}",
            metadata={k: a.get(k, "") for k in ["title", "url", "publishedAt"]} | 
                    {"source": a.get("source", {}).get("name", "")}
        ) for a in articles
    ]

def build_vectorstore(docs):
    return FAISS.from_documents(docs, embeddings)

def create_app():
    from core.news import fetch_news, detect_category
    from utils.cache import load_cache
    from service.gemini import ask_gemini
    
    g = StateGraph(NewsState)
    
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
    
    for name, func in nodes.items():
        g.add_node(name, func)
    
    edges = [("detect", "fetch"), ("fetch", "format"), ("format", "vector"),
             ("vector", "retrieve"), ("retrieve", "summarize"), ("summarize", END)]
    
    g.set_entry_point("detect")
    for start, end in edges:
        g.add_edge(start, end)
    
    return g.compile()