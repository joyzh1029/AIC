# mypy: disable - error - code = "no-untyped-def,misc"
import pathlib
import sys
import os
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import fastapi.exceptions

# Add the backend directory to Python path to import app modules
backend_dir = pathlib.Path(__file__).parent.parent.parent.parent / "app"
sys.path.append(str(backend_dir))

# Import LangGraph search agent
from agent.graph import graph
from agent.state import OverallState
from langchain_core.messages import HumanMessage

# Define the FastAPI app
app = FastAPI()

# Add root path redirect to /app
@app.get("/")
async def root():
    """Redirect root path to the frontend app"""
    return RedirectResponse(url="/app", status_code=302)

# Add favicon handler
@app.get("/favicon.ico")
async def favicon():
    """Handle favicon requests"""
    return Response(status_code=204)

# Add search endpoint using complete LangGraph Agent workflow
@app.post("/app/search")
async def search(request: Request):
    """Handle search requests using the complete LangGraph Agent workflow with Korean support"""
    try:
        body = await request.json()
        search_text = body.get("text", "")
        user_id = body.get("user_id", "")
        search_type = body.get("search_type", "web")
        
        # Create Korean-specific search prompt
        korean_search_prompt = f"""질문: {search_text}

이 질문에 대해 한국어로 웹 검색을 수행하고, 한국어로 답변해주세요. 
검색할 때는 한국어 키워드를 사용하고, 한국 사이트의 정보를 우선적으로 참고해주세요.
모든 검색 결과와 답변은 반드시 한국어로 작성해주세요.

Please search and respond in Korean language only. Use Korean search terms and prioritize Korean sources."""

        # Create complete initial state for LangGraph Agent (matching the studio interface)
        initial_state = {
            "messages": [HumanMessage(content=korean_search_prompt)],
            "search_query": [],  # Will be populated by generate_query node
            "web_research_result": [],  # Will be populated by web_research node
            "sources_gathered": [],  # Will be populated by web_research node
            "initial_search_query_count": 3,  # Number of initial search queries to generate
            "max_research_loops": 2,  # Maximum number of research iterations
            "research_loop_count": 0,  # Current research loop count
            "reasoning_model": "gemini-2.5-flash-preview-04-17"  # Model for reasoning tasks
        }
        
        # Configure the graph with Korean language preferences
        config = {
            "configurable": {
                "query_generator_model": "gemini-2.0-flash",
                "reasoning_model": "gemini-2.5-flash-preview-04-17", 
                "answer_model": "gemini-2.5-pro-preview-05-06",
                "number_of_initial_queries": 3,
                "max_research_loops": 2
            }
        }
        
        # Run the complete LangGraph search agent workflow
        # This will go through: generate_query -> web_research -> reflection -> finalize_answer
        final_result = await graph.ainvoke(initial_state, config=config)
        
        # Extract the final answer from the agent
        final_answer = ""
        if final_result.get("messages"):
            # Get the last AI message which contains the final answer
            for message in reversed(final_result["messages"]):
                if hasattr(message, 'content') and message.content:
                    final_answer = message.content
                    break
        
        # Extract search results and sources for frontend display
        search_results = []
        sources = final_result.get("sources_gathered", [])
        web_results = final_result.get("web_research_result", [])
        
        # Create structured results for frontend
        if web_results:
            for i, content in enumerate(web_results[:3]):  # Limit to 3 results
                # Extract title from content
                lines = content.split('\n')
                title = f"검색 결과 {i+1}: {search_text}"
                
                # Look for meaningful Korean title
                for line in lines[:3]:
                    line = line.strip()
                    if line and 10 < len(line) < 100:
                        if any('\uac00' <= char <= '\ud7af' for char in line):
                            title = line
                            break
                        elif not line.startswith(('http', '[', '#')):
                            title = line
                            break
                
                # Get snippet
                snippet = content[:300] + "..." if len(content) > 300 else content
                
                # Get source URL
                link = "https://example.com"
                if i < len(sources) and isinstance(sources[i], dict):
                    link = sources[i].get("value") or sources[i].get("url") or link
                
                search_results.append({
                    "title": title,
                    "snippet": snippet,
                    "link": link
                })
        
        # Create final response
        if final_answer or search_results:
            # Use the AI's final answer if available, otherwise format search results
            response_text = final_answer if final_answer else "검색을 완료했지만 결과를 처리하는 중 문제가 발생했습니다."
            
            return {
                "success": True,
                "results": search_results,
                "message": {
                    "text": response_text
                },
                "search_type": search_type,
                "query": search_text,
                "agent_response": final_answer,  # Include the complete agent response
                "research_summary": {
                    "total_queries": len(final_result.get("search_query", [])),
                    "research_loops": final_result.get("research_loop_count", 0),
                    "sources_count": len(sources)
                }
            }
        else:
            return {
                "success": False,
                "error": "No results generated",
                "message": {
                    "text": "죄송합니다. 검색 결과를 생성할 수 없었습니다."
                }
            }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Search error: {error_details}")  # For debugging
        
        return {
            "success": False,
            "error": str(e),
            "message": {
                "text": f"검색 중 오류가 발생했습니다: {str(e)}"
            }
        }

def create_frontend_router(build_dir="../frontend/dist"):
    """Creates a router to serve the React frontend.

    Args:
        build_dir: Path to the React build directory relative to this file.

    Returns:
        A Starlette application serving the frontend.
    """
    build_path = pathlib.Path(__file__).parent.parent.parent / build_dir
    static_files_path = build_path / "assets"  # Vite uses 'assets' subdir

    if not build_path.is_dir() or not (build_path / "index.html").is_file():
        print(
            f"WARN: Frontend build directory not found or incomplete at {build_path}. Serving frontend will likely fail."
        )
        # Return a dummy router if build isn't ready
        from starlette.routing import Route

        async def dummy_frontend(request):
            return Response(
                "Frontend not built. Run 'npm run build' in the frontend directory.",
                media_type="text/plain",
                status_code=503,
            )

        return Route("/{path:path}", endpoint=dummy_frontend)

    build_dir = pathlib.Path(build_dir)

    react = FastAPI(openapi_url="")
    react.mount(
        "/assets", StaticFiles(directory=static_files_path), name="static_assets"
    )

    @react.get("/{path:path}")
    async def handle_catch_all(request: Request, path: str):
        fp = build_path / path
        if not fp.exists() or not fp.is_file():
            fp = build_path / "index.html"
        return fastapi.responses.FileResponse(fp)

    return react


# Mount the frontend under /app to not conflict with the LangGraph API routes
app.mount(
    "/app",
    create_frontend_router(),
    name="frontend",
)
