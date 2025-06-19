# app/routers/search.py

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from langchain.schema.messages import HumanMessage
from ..agent.graph import graph
import json
import asyncio
import os

from ..nlp.llm import generate_response

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

@router.post("/stream")
async def search_stream_endpoint(request: Request):
    """流式搜索端点，使用Server-Sent Events (SSE)"""
    try:
        body = await request.json()
        query = body.get("query", "")
        if not query:
            return JSONResponse(
                status_code=400,
                content={"error": "Query parameter is required"}
            )

        initial_search_query_count = body.get("initial_search_query_count", 2)
        max_research_loops = body.get("max_research_loops", 2)
        reasoning_model = body.get("reasoning_model", "gpt-4o-mini")

        print("🔎 流式 검색 요청 수신:", query)

        if not os.getenv("GEMINI_API_KEY"):
            return JSONResponse(
                status_code=500,
                content={"error": "GEMINI_API_KEY is not configured"}
            )

        async def generate_search_stream():
            try:
                # 配置搜索参数
                config = {
                    "initial_search_query_count": initial_search_query_count,
                    "max_research_loops": max_research_loops,
                    "reasoning_model": reasoning_model
                }

                # 发送开始搜索状态
                start_data = {
                    "type": "update",
                    "event": {"status": "검색을 시작합니다..."}
                }
                yield f"data: {json.dumps(start_data, ensure_ascii=False)}\n\n"

                # 使用LangGraph的invoke方法（非流式）
                try:
                    result = graph.invoke(
                        {"messages": [HumanMessage(content=query)]},
                        config=config
                    )
                except Exception as e:
                    print(f"Graph invoke error: {str(e)}")
                    error_data = {
                        "type": "error",
                        "content": f"검색 중 오류가 발생했습니다: {str(e)}"
                    }
                    yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                    return
                
                # 发送搜索完成状态
                complete_data = {
                    "type": "update",
                    "event": {"status": "검색이 완료되었습니다."}
                }
                yield f"data: {json.dumps(complete_data, ensure_ascii=False)}\n\n"
                
                raw_list = result.get("web_research_result", [])
                
                if not raw_list:
                    # 发送错误消息
                    error_data = {
                        "type": "message",
                        "content": "검색 결과가 없습니다. 질문을 더 구체적으로 입력해 보세요."
                    }
                    yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                else:
                    try:
                        # 生成最终响应
                        response = await generate_response(
                            emotion="정보탐색",
                            user_text=query,
                            context={
                                "search_raw_list": raw_list,
                                "user_question": query
                            },
                            ai_mbti_persona=None
                        )
                        
                        # 发送最终消息
                        final_data = {
                            "type": "message",
                            "content": response
                        }
                        yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"
                    except Exception as e:
                        print(f"Response generation error: {str(e)}")
                        error_data = {
                            "type": "error",
                            "content": f"응답 생성 중 오류가 발생했습니다: {str(e)}"
                        }
                        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                        return

                # 发送完成信号
                finish_data = {
                    "type": "finish",
                    "content": "검색이 완료되었습니다."
                }
                yield f"data: {json.dumps(finish_data, ensure_ascii=False)}\n\n"

            except Exception as e:
                print(f"Stream generation error: {str(e)}")
                error_data = {
                    "type": "error",
                    "content": f"검색 스트림 생성 중 오류가 발생했습니다: {str(e)}"
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate_search_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )
    except Exception as e:
        print(f"Search endpoint error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"검색 엔드포인트 오류: {str(e)}"}
        )


