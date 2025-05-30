# FastAPI 서버 설정

from fastapi import FastAPI, Query
from core import create_app
from utils import save_cache

api = FastAPI()

@api.get("/ask_news")
async def ask_news(query: str = Query(..., description="요약할 뉴스 관련 질문")):
    try:
        app = create_app()
        state = app.invoke({"query": query})
        if state.get("articles"):
            save_cache(state["articles"])
        return {"result": state.get("answer", "처리 실패")}
    except Exception as e:
        return {"error": str(e)}