import os
import json
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# FastMCP 서버 초기화
mcp = FastMCP("todoist", port=8002)

# Todoist API 설정
TODOIST_API_URL = "https://api.todoist.com/rest/v2"
TODOIST_API_TOKEN = os.getenv("TODOIST_API_TOKEN", "")

# 보조 함수: 요청 헤더 가져오기
def get_headers():
    """Todoist API 요청 헤더 가져오기"""
    return {
        "Authorization": f"Bearer {TODOIST_API_TOKEN}",
        "Content-Type": "application/json"
    }

# 연결 테스트 도구
@mcp.tool()
def connect_todoist(api_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Todoist API에 연결하고 연결 상태 확인
    
    Args:
        api_token: Todoist API Token (선택사항, 제공하지 않으면 환경변수 사용)
    
    Returns:
        연결 상태와 사용자 정보를 포함한 딕셔너리
    """
    global TODOIST_API_TOKEN
    
    if api_token:
        TODOIST_API_TOKEN = api_token
    
    if not TODOIST_API_TOKEN:
        return {
            "success": False,
            "error": "API Token이 제공되지 않았습니다"
        }
    
    try:
        # 연결 테스트 및 사용자 정보 가져오기
        response = requests.get(
            f"{TODOIST_API_URL}/projects",
            headers=get_headers()
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Todoist에 성공적으로 연결되었습니다",
                "projects_count": len(response.json())
            }
        else:
            return {
                "success": False,
                "error": f"연결 실패: {response.status_code} - {response.text}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"연결 오류: {str(e)}"
        }

# 프로젝트 관리 도구
@mcp.tool()
def get_projects() -> Dict[str, Any]:
    """
    모든 Todoist 프로젝트 가져오기
    
    Returns:
        프로젝트 목록을 포함한 딕셔너리
    """
    try:
        response = requests.get(
            f"{TODOIST_API_URL}/projects",
            headers=get_headers()
        )
        
        if response.status_code == 200:
            projects = response.json()
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

@mcp.tool()
def create_project(name: str, color: str = "blue", is_favorite: bool = False) -> Dict[str, Any]:
    """
    새로운 Todoist 프로젝트 생성
    
    Args:
        name: 프로젝트 이름
        color: 프로젝트 색상 (기본값: blue)
        is_favorite: 즐겨찾기 여부 (기본값: False)
    
    Returns:
        생성된 프로젝트 정보
    """
    try:
        data = {
            "name": name,
            "color": color,
            "is_favorite": is_favorite
        }
        
        response = requests.post(
            f"{TODOIST_API_URL}/projects",
            headers=get_headers(),
            json=data
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "project": response.json()
            }
        else:
            return {
                "success": False,
                "error": f"프로젝트 생성 실패: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"요청 오류: {str(e)}"
        }

# 작업 관리 도구
@mcp.tool()
def get_tasks(project_id: Optional[str] = None, filter: Optional[str] = None) -> Dict[str, Any]:
    """
    작업 목록 가져오기
    
    Args:
        project_id: 프로젝트 ID (선택사항)
        filter: 필터 조건 (선택사항, 예: "today", "overdue")
    
    Returns:
        작업 목록
    """
    try:
        params = {}
        if project_id:
            params["project_id"] = project_id
        if filter:
            params["filter"] = filter
        
        response = requests.get(
            f"{TODOIST_API_URL}/tasks",
            headers=get_headers(),
            params=params
        )
        
        if response.status_code == 200:
            tasks = response.json()
            return {
                "success": True,
                "tasks": tasks,
                "count": len(tasks)
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

@mcp.tool()
def create_task(
    content: str,
    description: Optional[str] = None,
    project_id: Optional[str] = None,
    priority: int = 4,
    due_date: Optional[str] = None,
    labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    새 작업 생성
    
    Args:
        content: 작업 내용
        description: 작업 설명 (선택사항)
        project_id: 프로젝트 ID (선택사항)
        priority: 우선순위 (1-4, 1이 최고, 기본값 4)
        due_date: 마감일 (선택사항, 형식: "2024-12-31")
        labels: 라벨 목록 (선택사항)
    
    Returns:
        생성된 작업 정보
    """
    try:
        data = {
            "content": content,
            "priority": priority
        }
        
        if description:
            data["description"] = description
        if project_id:
            data["project_id"] = project_id
        if due_date:
            data["due_string"] = due_date
        if labels:
            data["labels"] = labels
        
        response = requests.post(
            f"{TODOIST_API_URL}/tasks",
            headers=get_headers(),
            json=data
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "task": response.json()
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

@mcp.tool()
def complete_task(task_id: str) -> Dict[str, Any]:
    """
    작업 완료
    
    Args:
        task_id: 작업 ID
    
    Returns:
        작업 결과
    """
    try:
        response = requests.post(
            f"{TODOIST_API_URL}/tasks/{task_id}/close",
            headers=get_headers()
        )
        
        if response.status_code == 204:
            return {
                "success": True,
                "message": f"작업 {task_id}가 완료되었습니다"
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

@mcp.tool()
def update_task(
    task_id: str,
    content: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[int] = None,
    due_date: Optional[str] = None,
    labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    작업 업데이트
    
    Args:
        task_id: 작업 ID
        content: 새로운 작업 내용 (선택사항)
        description: 새로운 작업 설명 (선택사항)
        priority: 새로운 우선순위 (선택사항)
        due_date: 새로운 마감일 (선택사항)
        labels: 새로운 라벨 목록 (선택사항)
    
    Returns:
        업데이트된 작업 정보
    """
    try:
        data = {}
        if content:
            data["content"] = content
        if description is not None:
            data["description"] = description
        if priority:
            data["priority"] = priority
        if due_date:
            data["due_string"] = due_date
        if labels is not None:
            data["labels"] = labels
        
        response = requests.post(
            f"{TODOIST_API_URL}/tasks/{task_id}",
            headers=get_headers(),
            json=data
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "task": response.json()
            }
        else:
            return {
                "success": False,
                "error": f"작업 업데이트 실패: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"요청 오류: {str(e)}"
        }

@mcp.tool()
def delete_task(task_id: str) -> Dict[str, Any]:
    """
    작업 삭제
    
    Args:
        task_id: 작업 ID
    
    Returns:
        작업 결과
    """
    try:
        response = requests.delete(
            f"{TODOIST_API_URL}/tasks/{task_id}",
            headers=get_headers()
        )
        
        if response.status_code == 204:
            return {
                "success": True,
                "message": f"작업 {task_id}가 삭제되었습니다"
            }
        else:
            return {
                "success": False,
                "error": f"작업 삭제 실패: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"요청 오류: {str(e)}"
        }

# 리소스 정의
@mcp.resource("todoist://today")
def get_today_tasks() -> str:
    """
    오늘의 작업 가져오기
    
    Returns:
        오늘의 작업을 마크다운 형식으로 반환
    """
    try:
        response = requests.get(
            f"{TODOIST_API_URL}/tasks",
            headers=get_headers(),
            params={"filter": "today"}
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
                    content += "\n"
            else:
                content += "오늘은 할 일이 없습니다. 잘 쉬세요! 🎉\n"
            
            return content
        else:
            return f"# 오류\n\n오늘의 작업을 가져올 수 없습니다: {response.status_code}"
    except Exception as e:
        return f"# 오류\n\n{str(e)}"

@mcp.resource("todoist://projects/{project_name}")
def get_project_tasks(project_name: str) -> str:
    """
    특정 프로젝트의 작업 가져오기
    
    Args:
        project_name: 프로젝트 이름
    
    Returns:
        프로젝트 작업을 마크다운 형식으로 반환
    """
    try:
        # 먼저 프로젝트 목록을 가져와서 해당 프로젝트 ID 찾기
        projects_response = requests.get(
            f"{TODOIST_API_URL}/projects",
            headers=get_headers()
        )
        
        if projects_response.status_code != 200:
            return f"# 오류\n\n프로젝트 목록을 가져올 수 없습니다"
        
        projects = projects_response.json()
        project = next((p for p in projects if p['name'].lower() == project_name.lower()), None)
        
        if not project:
            return f"# 오류\n\n프로젝트를 찾을 수 없습니다: {project_name}"
        
        # 프로젝트 작업 가져오기
        tasks_response = requests.get(
            f"{TODOIST_API_URL}/tasks",
            headers=get_headers(),
            params={"project_id": project['id']}
        )
        
        if tasks_response.status_code == 200:
            tasks = tasks_response.json()
            
            content = f"# {project['name']} 프로젝트 작업\n\n"
            content += f"총 {len(tasks)}개의 작업\n\n"
            
            for task in tasks:
                priority_emoji = {1: "🔴", 2: "🟠", 3: "🔵", 4: "⚪"}
                content += f"{priority_emoji.get(task['priority'], '⚪')} **{task['content']}**\n"
                if task.get('description'):
                    content += f"   {task['description']}\n"
                content += "\n"
            
            return content
        else:
            return f"# 오류\n\n프로젝트 작업을 가져올 수 없습니다"
    except Exception as e:
        return f"# 오류\n\n{str(e)}"

# 프롬프트 템플릿
@mcp.prompt()
def daily_planning_prompt() -> str:
    """일일 계획 수립을 위한 프롬프트 생성"""
    return """오늘의 일정 계획을 세우는 데 도움을 드리겠습니다.

다음 단계를 따라 진행하겠습니다:
1. 먼저 get_tasks(filter="today")를 사용하여 오늘 이미 있는 작업을 확인합니다
2. 오늘의 주요 목표와 우선순위에 대해 질문드리겠습니다
3. 답변에 따라 create_task를 사용하여 적절한 작업을 생성하고 적절한 우선순위를 설정합니다
4. 각 작업에 대해 합리적인 시간 배정을 합니다
5. 마지막으로 오늘의 일정 개요와 제안사항을 드립니다

다음 사항을 확인하겠습니다:
- 작업 설명이 명확하고 구체적인지
- 우선순위가 합리적으로 설정되었는지 (1이 최고, 4가 최저)
- 시간 배정이 너무 빡빡하지 않고 여유 시간이 있는지
- 작업 간의 의존 관계를 고려했는지"""

@mcp.prompt()
def weekly_review_prompt() -> str:
    """주간 회고를 위한 프롬프트 생성"""
    return """이번 주 작업 회고와 다음 주 계획을 도와드리겠습니다.

실행 단계:
1. get_tasks(filter="@7_days")를 사용하여 지난 7일간의 작업을 가져옵니다
2. 완료 상황과 미완료 원인을 분석합니다
3. get_projects()를 사용하여 모든 프로젝트 진행 상황을 확인합니다
4. 다음 주를 위한 개선 계획을 수립합니다
5. create_task를 사용하여 다음 주의 핵심 작업을 생성합니다

회고 요점:
- 이번 주에 완료한 중요한 작업들
- 연기된 작업들과 그 원인
- 프로젝트 진행이 예상대로 되었는지
- 다음 주에 중점적으로 관심을 가져야 할 것
- 작업 완료율을 높이는 방법"""

if __name__ == "__main__":
    # 서버 초기화 및 실행
    print(f"포트 8002에서 Todoist MCP 서버를 시작합니다...")
    print(f"TODOIST_API_TOKEN 환경변수가 설정되어 있는지 확인해주세요")
    mcp.run(transport='sse')
