"""
일정 관리 서비스 - Todoist MCP Server와 연동
"""
import json
import logging
import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ScheduleTask:
    """일정 작업 데이터 클래스"""
    content: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: int = 4
    project_id: Optional[str] = None
    labels: Optional[List[str]] = None

class ScheduleAgentService:
    """일정 관리 에이전트 서비스 - Todoist MCP Server와 연동"""
    
    def __init__(self):
        self.node_api_url = "http://localhost:3001"  # Node.js API 서버 URL
        self.conversation_history: Dict[str, List[Dict]] = {}
        self.session = None
        
    async def _get_session(self):
        """HTTP 세션 가져오기"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _call_todoist_api(self, endpoint: str, method: str = "GET", data: Dict = None):
        """Todoist MCP Server API 호출"""
        try:
            session = await self._get_session()
            url = f"{self.node_api_url}/api/mcp/todoist{endpoint}"
            
            logger.info(f"Calling Todoist API: {method} {url}")
            
            if method == "GET":
                async with session.get(url) as response:
                    return await response.json()
            elif method == "POST":
                async with session.post(url, json=data) as response:
                    return await response.json()
            elif method == "PUT":
                async with session.put(url, json=data) as response:
                    return await response.json()
            elif method == "DELETE":
                async with session.delete(url) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Todoist API 호출 오류: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _extract_task_from_message(self, message: str) -> Optional[ScheduleTask]:
        """메시지에서 작업 정보 추출"""
        # 일정 관련 키워드 패턴
        task_patterns = [
            r"(.+?)을?를?\s*(?:추가|등록|생성|만들|넣)(?:어?줘?|해?줘?|하자|해?라)",
            r"(.+?)(?:\s*일정|작업|할일|task)(?:을?를?)?\s*(?:추가|등록|생성|만들|넣)",
            r"(?:일정|작업|할일|task)(?:을?를?)?\s*(.+?)(?:으로?|로?)\s*(?:추가|등록|생성|만들|넣)",
            r"(.+?)(?:\s*해?야?\s*(?:해?|함|할|한다))",
            r"(.+?)(?:\s*예약|약속|미팅|회의)"
        ]
        
        for pattern in task_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                if len(content) > 3:  # 너무 짧은 내용 제외
                    # 날짜 추출
                    due_date = self._extract_date_from_message(message)
                    # 우선순위 추출
                    priority = self._extract_priority_from_message(message)
                    
                    return ScheduleTask(
                        content=content,
                        due_date=due_date,
                        priority=priority
                    )
        return None
    
    def _extract_date_from_message(self, message: str) -> Optional[str]:
        """메시지에서 날짜 정보 추출"""
        date_patterns = [
            r"(\d{4}-\d{2}-\d{2})",  # YYYY-MM-DD
            r"(\d{2}-\d{2})",        # MM-DD
            r"(오늘|today)",
            r"(내일|tomorrow)",
            r"(모레|day after tomorrow)",
            r"(\d+)일\s*후",
            r"다음\s*주",
            r"(\d+)월\s*(\d+)일"
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                if "오늘" in match.group(0) or "today" in match.group(0).lower():
                    return datetime.now().strftime("%Y-%m-%d")
                elif "내일" in match.group(0) or "tomorrow" in match.group(0).lower():
                    return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                elif "모레" in match.group(0):
                    return (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
                elif "일 후" in match.group(0):
                    days = int(re.search(r"(\d+)", match.group(0)).group(1))
                    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
                elif match.group(0).count("-") == 2:  # YYYY-MM-DD
                    return match.group(0)
                elif match.group(0).count("-") == 1:  # MM-DD
                    current_year = datetime.now().year
                    return f"{current_year}-{match.group(0)}"
        
        return None
    
    def _extract_priority_from_message(self, message: str) -> int:
        """메시지에서 우선순위 추출 (1=매우 높음, 2=높음, 3=보통, 4=낮음)"""
        if any(word in message for word in ["긴급", "urgent", "중요", "important", "우선"]):
            return 1
        elif any(word in message for word in ["높음", "high", "빨리", "서둘"]):
            return 2
        elif any(word in message for word in ["보통", "normal", "일반"]):
            return 3
        else:
            return 4
    
    def _is_schedule_related(self, message: str) -> bool:
        """메시지가 일정 관련인지 확인"""
        schedule_keywords = [
            "일정", "스케줄", "schedule", "할일", "todo", "task", "작업",
            "미팅", "meeting", "회의", "약속", "appointment", "예약",
            "추가", "등록", "생성", "만들", "넣", "삭제", "제거", "완료",
            "오늘", "내일", "모레", "다음주", "이번주", "today", "tomorrow"
        ]
        
        return any(keyword in message.lower() for keyword in schedule_keywords)
    
    async def process_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """사용자 메시지 처리"""
        try:
            # 대화 기록 업데이트
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            self.conversation_history[user_id].append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            
            # 일정 관련 메시지인지 확인
            if not self._is_schedule_related(message):
                response = "일정 관리와 관련된 요청을 말씀해 주세요. 예: '내일 회의 일정 추가해줘', '오늘 할일 보여줘' 등"
                self.conversation_history[user_id].append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().isoformat()
                })
                return {"success": True, "response": response}
            
            # 작업 생성 요청 처리
            task = self._extract_task_from_message(message)
            if task:
                result = await self._create_todoist_task(task)
                if result.get("success"):
                    response = f"✅ 일정이 Todoist에 추가되었습니다!\n📝 작업: {task.content}"
                    if task.due_date:
                        response += f"\n📅 날짜: {task.due_date}"
                    if task.priority < 4:
                        priority_names = {1: "매우 높음", 2: "높음", 3: "보통"}
                        response += f"\n⚡ 우선순위: {priority_names.get(task.priority, '보통')}"
                else:
                    response = f"❌ 일정 추가 실패: {result.get('error', '알 수 없는 오류')}"
            
            # 작업 목록 조회 요청 처리
            elif any(word in message for word in ["보여줘", "알려줘", "목록", "list", "조회"]):
                tasks = await self._get_todoist_tasks()
                if tasks.get("success"):
                    task_list = tasks.get("data", [])
                    if task_list:
                        response = "📋 현재 할일 목록:\n\n"
                        for i, task in enumerate(task_list[:10], 1):  # 최대 10개만 표시
                            response += f"{i}. {task.get('content', 'N/A')}"
                            if task.get('due'):
                                response += f" (마감: {task['due'].get('date', 'N/A')})"
                            response += "\n"
                    else:
                        response = "📋 현재 등록된 할일이 없습니다."
                else:
                    response = f"❌ 할일 목록 조회 실패: {tasks.get('error', '알 수 없는 오류')}"
            
            # 프로젝트 목록 조회
            elif any(word in message for word in ["프로젝트", "project"]):
                projects = await self._get_todoist_projects()
                if projects.get("success"):
                    project_list = projects.get("data", [])
                    if project_list:
                        response = "📁 프로젝트 목록:\n\n"
                        for i, project in enumerate(project_list, 1):
                            response += f"{i}. {project.get('name', 'N/A')}\n"
                    else:
                        response = "📁 현재 등록된 프로젝트가 없습니다."
                else:
                    response = f"❌ 프로젝트 목록 조회 실패: {projects.get('error', '알 수 없는 오류')}"
            
            else:
                response = """📅 일정 관리 도우미입니다!
                
다음과 같은 명령을 사용할 수 있습니다:
• "내일 회의 일정 추가해줘" - 새 일정 추가
• "오늘 할일 보여줘" - 할일 목록 조회  
• "프로젝트 목록 보여줘" - 프로젝트 조회
• "긴급 보고서 작성 추가해줘" - 우선순위 설정

어떤 일정을 관리하고 싶으신가요?"""
            
            # 응답 기록
            self.conversation_history[user_id].append({
                "role": "assistant", 
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            return {"success": True, "response": response}
            
        except Exception as e:
            logger.error(f"메시지 처리 오류: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _create_todoist_task(self, task: ScheduleTask) -> Dict[str, Any]:
        """Todoist에 작업 생성"""
        data = {
            "content": task.content,
            "priority": task.priority
        }
        
        if task.description:
            data["description"] = task.description
        if task.due_date:
            data["due_date"] = task.due_date
        if task.project_id:
            data["project_id"] = task.project_id
        if task.labels:
            data["labels"] = task.labels
            
        return await self._call_todoist_api("/tasks", "POST", data)
    
    async def _get_todoist_tasks(self, project_id: str = None) -> Dict[str, Any]:
        """Todoist 작업 목록 조회"""
        endpoint = "/tasks"
        if project_id:
            endpoint += f"?project_id={project_id}"
        return await self._call_todoist_api(endpoint, "GET")
    
    async def _get_todoist_projects(self) -> Dict[str, Any]:
        """Todoist 프로젝트 목록 조회"""
        return await self._call_todoist_api("/projects", "GET")
    
    async def get_events(self, user_id: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        """일정 목록 조회"""
        try:
            result = await self._get_todoist_tasks()
            if result.get("success"):
                tasks = result.get("data", [])
                events = []
                for task in tasks:
                    event = {
                        "id": task.get("id"),
                        "title": task.get("content"),
                        "description": task.get("description", ""),
                        "due_date": task.get("due", {}).get("date") if task.get("due") else None,
                        "priority": task.get("priority", 4),
                        "completed": task.get("is_completed", False)
                    }
                    events.append(event)
                return events
            else:
                logger.error(f"일정 조회 실패: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"일정 조회 오류: {str(e)}")
            return []
    
    def clear_conversation(self, user_id: str):
        """대화 기록 초기화"""
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
            logger.info(f"사용자 {user_id}의 대화 기록이 초기화되었습니다")
    
    async def close(self):
        """서비스 종료 시 리소스 정리"""
        if self.session:
            await self.session.close() 