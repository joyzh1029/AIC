#!/usr/bin/env python3
"""
Todoist MCP 서버 - 공식 MCP Python SDK 사용
"""

import os
import json
import requests
import asyncio
import logging
from typing import List, Dict, Optional, Any, Sequence
from datetime import datetime
import time

from mcp.server.fastmcp import FastMCP
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Resource,
    ListResourcesRequest,
    ListResourcesResult,
    ReadResourceRequest,
    ReadResourceResult,
    TextResourceContents,
    Prompt,
    ListPromptsRequest,
    ListPromptsResult,
    GetPromptRequest,
    GetPromptResult,
    PromptMessage,
    Role
)

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("todoist-mcp")

# Todoist API 설정
TODOIST_API_URL = "https://api.todoist.com/rest/v2"
TODOIST_API_TOKEN = os.getenv("TODOIST_API_TOKEN", "")

# FastMCP 서버 인스턴스 생성 (올바른 초기화)
print("🚀 Todoist MCP 서버 초기화")
print("📦 공식 MCP SDK 버전")
print(f"🔑 API Token 상태: {'설정됨' if TODOIST_API_TOKEN else '설정되지 않음'}")

# 서버 초기화를 async 함수로 래핑
async def create_mcp_server():
    """FastMCP 서버를 비동기적으로 생성하고 초기화"""
    server = FastMCP("todoist-mcp")
    
    # 서버 초기화 완료를 위한 약간의 지연
    await asyncio.sleep(0.5)
    
    logger.info("✅ FastMCP 서버 초기화 완료")
    return server

# 전역 서버 인스턴스 (나중에 초기화됨)
mcp = None

# 보조 함수
def get_headers():
    """Todoist API 요청 헤더 가져오기"""
    if not TODOIST_API_TOKEN:
        raise ValueError("TODOIST_API_TOKEN이 설정되지 않음")
    return {
        "Authorization": f"Bearer {TODOIST_API_TOKEN}",
        "Content-Type": "application/json"
    }

def safe_api_call(func_name: str, *args, **kwargs):
    """안전한 API 호출 래퍼"""
    try:
        return eval(f"{func_name}(*args, **kwargs)")
    except Exception as e:
        logger.error(f"❌ {func_name} 호출 오류: {str(e)}")
        return {
            "success": False,
            "error": f"{func_name} 실행 중 오류: {str(e)}"
        }

# 도구 정의 - 서버 초기화 후에 등록됨
def register_tools(server):
    """모든 도구를 서버에 등록"""
    
    @server.tool()
    def connect_todoist(api_token: str = "") -> str:
        """Todoist API에 연결 및 API Token 설정"""
        try:
            result = handle_connect_todoist({"api_token": api_token})
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @server.tool()
    def get_projects() -> str:
        """모든 프로젝트 목록 가져오기"""
        try:
            result = handle_get_projects()
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @server.tool()
    def get_tasks(project_id: str = "", filter_query: str = "") -> str:
        """작업 목록 가져오기 (프로젝트 ID 또는 필터로)"""
        try:
            result = handle_get_tasks({"project_id": project_id, "filter_query": filter_query})
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @server.tool()
    def create_task(content: str, description: str = "", priority: int = 4, due_date: str = "") -> str:
        """새 작업 생성"""
        try:
            result = handle_create_task({
                "content": content,
                "description": description, 
                "priority": priority,
                "due_date": due_date
            })
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @server.tool()
    def complete_task(task_id: str) -> str:
        """작업 완료 처리"""
        try:
            result = handle_complete_task({"task_id": task_id})
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

    @server.tool()
    def test_server() -> str:
        """서버 연결 및 상태 테스트"""
        try:
            result = {
                "success": True,
                "message": "FastMCP 서버가 정상적으로 작동 중입니다",
                "server_name": "todoist-mcp",
                "version": "1.9.3",
                "timestamp": datetime.now().isoformat(),
                "transport": "streamable-http",
                "api_token_status": "설정됨" if TODOIST_API_TOKEN else "설정되지 않음"
            }
            logger.info("✅ 서버 테스트 성공")
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
    
    logger.info("✅ 모든 도구가 등록되었습니다")

# 도구 구현 함수
def handle_connect_todoist(arguments: dict) -> dict:
    """Todoist 연결 처리"""
    global TODOIST_API_TOKEN
    
    api_token = arguments.get("api_token")
    if api_token:
        TODOIST_API_TOKEN = api_token
        logger.info("✅ 제공된 API Token 사용")
    
    if not TODOIST_API_TOKEN:
        return {
            "success": False,
            "error": "API Token이 제공되지 않음",
            "message": "TODOIST_API_TOKEN 환경 변수를 설정하거나 호출 시 api_token 매개변수를 제공하세요"
        }
    
    try:
        logger.info("🌐 Todoist API 연결 테스트 중...")
        response = requests.get(
            f"{TODOIST_API_URL}/projects",
            headers=get_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            projects = response.json()
            result = {
                "success": True,
                "message": "Todoist API에 성공적으로 연결됨",
                "projects_count": len(projects),
                "server_name": "todoist-mcp",
                "api_url": TODOIST_API_URL
            }
            logger.info(f"✅ Todoist 연결 성공, {len(projects)}개의 프로젝트 발견")
            return result
        else:
            error_msg = f"API 요청 실패: {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    except Exception as e:
        error_msg = f"연결 오류: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }

def handle_get_projects() -> dict:
    """프로젝트 목록 가져오기"""
    if not TODOIST_API_TOKEN:
        return {
            "success": False,
            "error": "API Token이 설정되지 않음, 먼저 connect_todoist를 호출하세요"
        }
    
    try:
        response = requests.get(
            f"{TODOIST_API_URL}/projects",
            headers=get_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            projects = response.json()
            logger.info(f"✅ {len(projects)}개의 프로젝트를 가져왔습니다")
            return {
                "success": True,
                "projects": projects,
                "count": len(projects)
            }
        else:
            return {
                "success": False,
                "error": f"프로젝트 가져오기 실패: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"요청 오류: {str(e)}"
        }

def handle_get_tasks(arguments: dict) -> dict:
    """작업 목록 가져오기"""
    if not TODOIST_API_TOKEN:
        return {
            "success": False,
            "error": "API Token이 설정되지 않음, 먼저 connect_todoist를 호출하세요"
        }
    
    project_id = arguments.get("project_id")
    filter_query = arguments.get("filter_query")
    
    try:
        params = {}
        if project_id:
            params["project_id"] = project_id
        if filter_query:
            params["filter"] = filter_query
        
        response = requests.get(
            f"{TODOIST_API_URL}/tasks",
            headers=get_headers(),
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            tasks = response.json()
            logger.info(f"✅ {len(tasks)}개의 작업을 가져왔습니다")
            return {
                "success": True,
                "tasks": tasks,
                "count": len(tasks),
                "filter_applied": filter_query,
                "project_id": project_id
            }
        else:
            return {
                "success": False,
                "error": f"작업 가져오기 실패: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"요청 오류: {str(e)}"
        }

def handle_create_task(arguments: dict) -> dict:
    """작업 생성"""
    if not TODOIST_API_TOKEN:
        return {
            "success": False,
            "error": "API Token이 설정되지 않음, 먼저 connect_todoist를 호출하세요"
        }
    
    content = arguments.get("content")
    if not content:
        return {
            "success": False,
            "error": "필수 매개변수 누락: content"
        }
    
    description = arguments.get("description")
    priority = arguments.get("priority", 4)
    due_date = arguments.get("due_date")
    
    try:
        data = {
            "content": content,
            "priority": priority
        }
        
        if description:
            data["description"] = description
        if due_date:
            data["due_string"] = due_date
        
        response = requests.post(
            f"{TODOIST_API_URL}/tasks",
            headers=get_headers(),
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            task = response.json()
            logger.info(f"✅ 작업 생성 성공, ID: {task.get('id')}")
            return {
                "success": True,
                "task": task,
                "message": f"작업 생성 성공: {content}"
            }
        else:
            return {
                "success": False,
                "error": f"작업 생성 실패: {response.status_code} - {response.text}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"요청 오류: {str(e)}"
        }

def handle_complete_task(arguments: dict) -> dict:
    """작업 완료"""
    if not TODOIST_API_TOKEN:
        return {
            "success": False,
            "error": "API Token이 설정되지 않음, 먼저 connect_todoist를 호출하세요"
        }
    
    task_id = arguments.get("task_id")
    if not task_id:
        return {
            "success": False,
            "error": "필수 매개변수 누락: task_id"
        }
    
    try:
        response = requests.post(
            f"{TODOIST_API_URL}/tasks/{task_id}/close",
            headers=get_headers(),
            timeout=10
        )
        
        if response.status_code == 204:
            logger.info(f"✅ 작업 {task_id} 완료됨")
            return {
                "success": True,
                "message": f"작업 {task_id} 완료됨"
            }
        else:
            return {
                "success": False,
                "error": f"작업 완료 실패: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"요청 오류: {str(e)}"
        }

# 리소스 등록 함수
def register_resources(server):
    """모든 리소스를 서버에 등록"""
    
    @server.resource("todoist://status")
    def status() -> str:
        """서버 상태 및 설정 정보 표시"""
        content = "# Todoist MCP 서버 상태\n\n"
        content += f"- **서버 이름**: todoist-mcp\n"
        content += f"- **SDK**: 공식 MCP Python SDK\n"
        content += f"- **API Token**: {'✅ 설정됨' if TODOIST_API_TOKEN else '❌ 설정되지 않음'}\n"
        content += f"- **상태**: 🟢 실행 중\n"
        content += f"- **시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        content += "## 사용 가능한 도구\n\n"
        content += "1. `connect_todoist` - Todoist API에 연결\n"
        content += "2. `get_projects` - 프로젝트 목록 가져오기\n"
        content += "3. `get_tasks` - 작업 목록 가져오기\n"
        content += "4. `create_task` - 새 작업 생성\n"
        content += "5. `complete_task` - 작업 완료\n"
        content += "6. `test_server` - 서버 연결 테스트\n"
        
        return content

    @server.resource("todoist://today")
    def today() -> str:
        """오늘의 모든 작업 가져오기"""
        if not TODOIST_API_TOKEN:
            return "# 오류\n\nAPI Token이 설정되지 않음, 먼저 connect_todoist 도구를 호출하세요."
        
        try:
            response = requests.get(
                f"{TODOIST_API_URL}/tasks",
                headers=get_headers(),
                params={"filter": "today"},
                timeout=10
            )
            
            if response.status_code == 200:
                tasks = response.json()
                
                content = "# 오늘의 작업\n\n"
                content += f"총 {len(tasks)}개의 작업\n\n"
                
                if tasks:
                    for task in tasks:
                        priority_emoji = {1: "🔴", 2: "🟠", 3: "🔵", 4: "⚪"}
                        content += f"{priority_emoji.get(task['priority'], '⚪')} **{task['content']}**\n"
                        if task.get('description'):
                            content += f"   {task['description']}\n"
                        if task.get('due'):
                            content += f"   📅 {task['due']['string']}\n"
                        content += f"   ID: {task['id']}\n\n"
                else:
                    content += "오늘은 작업이 없습니다, 잘 쉬세요! 🎉\n"
                
                return content
            else:
                return f"# 오류\n\n오늘의 작업을 가져올 수 없음: {response.status_code}"
        except Exception as e:
            return f"# 오류\n\n{str(e)}"
    
    logger.info("✅ 모든 리소스가 등록되었습니다")

# 프롬프트 등록 함수
def register_prompts(server):
    """모든 프롬프트를 서버에 등록"""
    
    @server.prompt()
    def daily_planning() -> GetPromptResult:
        """일일 계획 수립 도움"""
        messages = [
            PromptMessage(
                role=Role.user,
                content=TextContent(
                    type="text",
                    text="""오늘의 계획을 세우는 데 도움을 드리겠습니다.

단계:
1. 먼저 get_tasks(filter_query="today")를 사용하여 오늘의 기존 작업 확인
2. 주요 목표와 우선순위 문의  
3. 답변에 따라 create_task를 사용하여 적절한 작업 생성 및 우선순위 설정
4. 각 작업에 합리적인 시간 할당
5. 마지막으로 오늘의 계획 개요 및 제안 제공

확인 사항:
- 작업 설명이 명확하고 구체적인가
- 우선순위 설정이 합리적인가 (1이 최고, 4가 최저)
- 시간 배정이 합리적이고 여유 시간이 있는가
- 작업 간의 의존성을 고려했는가"""
                )
            )
        ]
        
        return GetPromptResult(messages=messages)

    @server.prompt()
    def quick_task(task_content: str) -> GetPromptResult:
        """빠른 작업 생성 프롬프트"""
        messages = [
            PromptMessage(
                role=Role.user,
                content=TextContent(
                    type="text",
                    text=f"""작업 생성을 도와드리겠습니다: {task_content}

알려주세요:
1. 작업의 자세한 설명은 무엇인가요?
2. 우선순위는 어떻게 하시겠습니까? (1=최고, 4=최저)  
3. 마감일이 있나요?

create_task 도구를 사용하여 이 작업을 생성해드리겠습니다."""
                )
            )
        ]
        
        return GetPromptResult(messages=messages)
    
    logger.info("✅ 모든 프롬프트가 등록되었습니다")

async def main():
    """메인 함수 - 비동기 초기화"""
    global mcp
    
    print("\n" + "="*50)
    print("🚀 Todoist MCP 서버 시작 (공식 SDK)")
    print("="*50)
    print(f"🔧 전송 프로토콜: FastMCP")
    print(f"🛠️  등록된 도구 수: 6")
    print(f"📚 등록된 리소스 수: 2")
    print(f"💬 등록된 프롬프트 수: 2")
    
    if not TODOIST_API_TOKEN:
        print(f"⚠️  경고: TODOIST_API_TOKEN 환경 변수가 설정되지 않음")
        print(f"💡 나중에 connect_todoist 도구를 통해 API Token을 제공할 수 있습니다")
    else:
        print(f"✅ TODOIST_API_TOKEN 설정됨")
    
    print("\n🎯 서버 초기화 중...\n")
    
    try:
        # FastMCP 서버 비동기 생성
        print("🔧 FastMCP 인스턴스 생성 중...")
        mcp = await create_mcp_server()
        
        # 도구 등록
        print("🛠️ 도구 등록 중...")
        register_tools(mcp)
        
        # 리소스 등록
        print("📚 리소스 등록 중...")
        register_resources(mcp)
        
        # 프롬프트 등록
        print("💬 프롬프트 등록 중...")
        register_prompts(mcp)
        
        print("✅ 모든 구성 요소 등록 완료!")
        
        # 추가 초기화 시간
        await asyncio.sleep(1)
        
        print("🎉 Todoist MCP 서버가 시작되었습니다!")
        print("💡 FastMCP 서버 실행 중...")
        print("🌐 전송 방식: streamable-http")
        print("⏳ 클라이언트 연결 대기 중...")
        
    except Exception as e:
        logger.error(f"❌ FastMCP 서버 초기화 오류: {e}")
        import traceback
        traceback.print_exc()
        raise

def run_server():
    """서버 실행 함수"""
    # 비동기 초기화 실행
    asyncio.run(main())
    
    # 서버 실행 (동기적으로)
    if mcp:
        mcp.run(transport="streamable-http")
    else:
        raise RuntimeError("서버가 초기화되지 않았습니다")

if __name__ == "__main__":
    try:
        # 서버 실행
        run_server()
    except KeyboardInterrupt:
        print("\n🛑 서버가 중지되었습니다")
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")
        import traceback
        traceback.print_exc() 