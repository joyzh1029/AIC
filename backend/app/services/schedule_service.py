# app/services/schedule_service.py
import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool, StructuredTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import SystemMessage, HumanMessage

# 데이터 모델
class EventStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ScheduleEvent(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    participants: List[str] = Field(default_factory=list)
    status: EventStatus = EventStatus.PENDING
    reminder_minutes: Optional[int] = 30
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ScheduleDatabase:
    """간단한 메모리 데이터베이스"""
    def __init__(self):
        self.events: Dict[str, ScheduleEvent] = {}
        self.next_id = 1
    
    def create_event(self, event_data: dict) -> ScheduleEvent:
        event_id = f"event_{self.next_id}"
        self.next_id += 1
        
        event = ScheduleEvent(
            id=event_id,
            **event_data
        )
        self.events[event_id] = event
        return event
    
    def get_event(self, event_id: str) -> Optional[ScheduleEvent]:
        return self.events.get(event_id)
    
    def update_event(self, event_id: str, updates: dict) -> Optional[ScheduleEvent]:
        if event_id in self.events:
            event = self.events[event_id]
            for key, value in updates.items():
                if hasattr(event, key):
                    setattr(event, key, value)
            event.updated_at = datetime.now()
            return event
        return None
    
    def delete_event(self, event_id: str) -> bool:
        if event_id in self.events:
            del self.events[event_id]
            return True
        return False
    
    def list_events(self, start_date: Optional[datetime] = None, 
                   end_date: Optional[datetime] = None) -> List[ScheduleEvent]:
        events = list(self.events.values())
        
        if start_date:
            events = [e for e in events if e.start_time >= start_date]
        if end_date:
            events = [e for e in events if e.end_time <= end_date]
        
        return sorted(events, key=lambda x: x.start_time)

class ScheduleAgentService:
    """일정 관리 Agent 서비스"""
    
    def __init__(self):
        self.db = ScheduleDatabase()
        self.conversation_histories: Dict[str, ConversationBufferMemory] = {}
        self.agent_executor = self._create_agent()
    
    def _create_tools(self):
        """LangChain 도구 생성"""
        
        def create_schedule_event(
            title: str,
            start_time: str,
            end_time: str,
            description: Optional[str] = None,
            location: Optional[str] = None,
            participants: Optional[List[str]] = None,
            reminder_minutes: Optional[int] = 30
        ) -> str:
            """새로운 일정 이벤트 생성"""
            try:
                event_data = {
                    "title": title,
                    "start_time": datetime.fromisoformat(start_time),
                    "end_time": datetime.fromisoformat(end_time),
                    "description": description,
                    "location": location,
                    "participants": participants or [],
                    "reminder_minutes": reminder_minutes
                }
                
                event = self.db.create_event(event_data)
                return f"성공적으로 일정을 생성했습니다: {event.title}, ID: {event.id}, 시간: {event.start_time.strftime('%Y-%m-%d %H:%M')} - {event.end_time.strftime('%H:%M')}"
            except Exception as e:
                return f"일정 생성 실패: {str(e)}"
        
        def query_schedule_events(
            date: Optional[str] = None,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None
        ) -> str:
            """일정 이벤트 조회"""
            try:
                if date:
                    target_date = datetime.fromisoformat(date).date()
                    start_dt = datetime.combine(target_date, datetime.min.time())
                    end_dt = datetime.combine(target_date, datetime.max.time())
                elif start_date and end_date:
                    start_dt = datetime.fromisoformat(start_date)
                    end_dt = datetime.fromisoformat(end_date)
                else:
                    start_dt = datetime.now()
                    end_dt = start_dt + timedelta(days=7)
                
                events = self.db.list_events(start_dt, end_dt)
                
                if not events:
                    return "해당 기간에 일정이 없습니다."
                
                result = "다음 일정들을 찾았습니다:\n"
                for event in events:
                    result += f"\n- {event.title} (ID: {event.id})\n"
                    result += f"  시간: {event.start_time.strftime('%Y-%m-%d %H:%M')} - {event.end_time.strftime('%H:%M')}\n"
                    if event.description:
                        result += f"  설명: {event.description}\n"
                    if event.location:
                        result += f"  장소: {event.location}\n"
                    result += f"  상태: {event.status}\n"
                
                return result
            except Exception as e:
                return f"일정 조회 실패: {str(e)}"
        
        def update_schedule_event(
            event_id: str,
            title: Optional[str] = None,
            start_time: Optional[str] = None,
            end_time: Optional[str] = None,
            description: Optional[str] = None,
            location: Optional[str] = None,
            status: Optional[str] = None
        ) -> str:
            """일정 이벤트 업데이트"""
            try:
                updates = {}
                if title:
                    updates["title"] = title
                if start_time:
                    updates["start_time"] = datetime.fromisoformat(start_time)
                if end_time:
                    updates["end_time"] = datetime.fromisoformat(end_time)
                if description is not None:
                    updates["description"] = description
                if location is not None:
                    updates["location"] = location
                if status:
                    updates["status"] = EventStatus(status)
                
                event = self.db.update_event(event_id, updates)
                if event:
                    return f"일정을 성공적으로 업데이트했습니다: {event.title} (ID: {event.id})"
                else:
                    return f"ID {event_id}에 해당하는 일정을 찾을 수 없습니다."
            except Exception as e:
                return f"일정 업데이트 실패: {str(e)}"
        
        def delete_schedule_event(event_id: str) -> str:
            """일정 이벤트 삭제"""
            try:
                event = self.db.get_event(event_id)
                if event:
                    if self.db.delete_event(event_id):
                        return f"일정을 성공적으로 삭제했습니다: {event.title} (ID: {event_id})"
                return f"ID {event_id}에 해당하는 일정을 찾을 수 없습니다."
            except Exception as e:
                return f"일정 삭제 실패: {str(e)}"
        
        def check_schedule_conflicts(
            start_time: str,
            end_time: str,
            exclude_event_id: Optional[str] = None
        ) -> str:
            """일정 충돌 확인"""
            try:
                start_dt = datetime.fromisoformat(start_time)
                end_dt = datetime.fromisoformat(end_time)
                
                events = self.db.list_events()
                conflicts = []
                
                for event in events:
                    if exclude_event_id and event.id == exclude_event_id:
                        continue
                    
                    if (start_dt < event.end_time and end_dt > event.start_time):
                        conflicts.append(event)
                
                if conflicts:
                    result = "다음 일정과 충돌이 있습니다:\n"
                    for event in conflicts:
                        result += f"- {event.title}: {event.start_time.strftime('%Y-%m-%d %H:%M')} - {event.end_time.strftime('%H:%M')}\n"
                    return result
                else:
                    return "일정 충돌이 없습니다."
            except Exception as e:
                return f"충돌 확인 실패: {str(e)}"
        
        return [
            StructuredTool.from_function(
                func=create_schedule_event,
                name="create_event",
                description="새로운 일정을 생성합니다. 제목, 시작 시간, 종료 시간이 필요합니다. 시간 형식: YYYY-MM-DD HH:MM:SS"
            ),
            StructuredTool.from_function(
                func=query_schedule_events,
                name="query_events",
                description="일정을 조회합니다. 날짜나 날짜 범위를 지정할 수 있습니다. 날짜 형식: YYYY-MM-DD"
            ),
            StructuredTool.from_function(
                func=update_schedule_event,
                name="update_event",
                description="기존 일정을 업데이트합니다. 이벤트 ID와 변경할 필드가 필요합니다."
            ),
            StructuredTool.from_function(
                func=delete_schedule_event,
                name="delete_event",
                description="일정을 삭제합니다. 이벤트 ID가 필요합니다."
            ),
            StructuredTool.from_function(
                func=check_schedule_conflicts,
                name="check_conflicts",
                description="지정된 시간에 일정 충돌이 있는지 확인합니다."
            )
        ]
    
    def _create_agent(self):
        """LangChain Agent 생성"""
        # 환경 변수에서 API 키 가져오기
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다.")
            
        # Gemini API 모델 설정 - 정확한 모델명 사용
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",  # 최신 모델명으로 업데이트
            temperature=0,
            google_api_key=google_api_key
        )
        
        system_prompt = """당신은 전문적인 일정 관리 비서입니다. 사용자의 일정을 관리하는 것이 당신의 임무입니다.

당신이 할 수 있는 일:
1. 새로운 일정 생성
2. 기존 일정 조회
3. 일정 정보 업데이트
4. 일정 삭제
5. 일정 충돌 확인

사용자 요청을 처리할 때:
- 사용자의 구체적인 요구사항을 파악하세요
- 일정을 생성하기 전에 충돌을 확인하세요
- 명확한 언어로 작업 결과를 확인해주세요
- 정보가 불완전한 경우 누락된 정보를 요청하세요
- 시간 형식은 YYYY-MM-DD HH:MM:SS여야 합니다

현재 시간: {current_time}
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad")
        ])
        
        tools = self._create_tools()
        agent = create_openai_tools_agent(llm, tools, prompt)
        
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
    
    async def process_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """사용자 메시지 처리"""
        if user_id not in self.conversation_histories:
            self.conversation_histories[user_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        
        memory = self.conversation_histories[user_id]
        
        try:
            result = await asyncio.to_thread(
                self.agent_executor.invoke,
                {
                    "input": message,
                    "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "chat_history": memory.chat_memory.messages
                }
            )
            
            memory.chat_memory.add_user_message(message)
            memory.chat_memory.add_ai_message(result["output"])
            
            return {
                "success": True,
                "response": result["output"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_events(self, user_id: str, start_date: Optional[str] = None, 
                        end_date: Optional[str] = None) -> List[dict]:
        """이벤트 목록 가져오기"""
        try:
            start_dt = datetime.fromisoformat(start_date) if start_date else None
            end_dt = datetime.fromisoformat(end_date) if end_date else None
            
            events = self.db.list_events(start_dt, end_dt)
            return [event.dict() for event in events]
        except Exception as e:
            raise Exception(f"이벤트 가져오기 실패: {str(e)}")
    
    def clear_conversation(self, user_id: str):
        """대화 기록 지우기"""
        if user_id in self.conversation_histories:
            del self.conversation_histories[user_id]