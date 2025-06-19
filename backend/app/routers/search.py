# app/routers/search.py

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from langchain.schema.messages import HumanMessage
from agent.graph import graph

from app.nlp.llm import generate_response

router = APIRouter(prefix="/search", tags=["Search"])

@router.post("/query")
async def search_endpoint(request: Request):
    body = await request.json()
    query = body.get("query", "")

    print("🔎 검색 요청 수신:", query)

    result = graph.invoke({"messages": [HumanMessage(content=query)]})
    raw_list = result.get("web_research_result", [])

    if not raw_list:
        return JSONResponse(content={
            "success": False,
            "mode": "search",
            "message": "검색 결과가 없습니다. 질문을 더 구체적으로 입력해 보세요.",
            "text": query
        })

    response = await generate_response(
        emotion="정보탐색",
        user_text=query,
        context={
            "search_raw_list": raw_list,
            "user_question": query
        },
        ai_mbti_persona=None  # 기본 페르소나 사용
    )

    return JSONResponse(content={
        "success": True,
        "mode": "search",
        "response": response,
        "summary": "\n\n".join(raw_list),
        "text": query
    })


