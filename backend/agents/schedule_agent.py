from langchain.agents import Tool
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from crewai import Agent, Task, Crew
from typing import List, Dict, Any, Optional
import datetime
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

# CSV 데이터베이스와 유틸리티 클래스 가져오기
from db.csv_database import CSVDatabase, ScheduleCSV
from utils.schedule_utils import ScheduleUtils

# 환경 변수 로드
load_dotenv()

class ScheduleEvent(BaseModel):
    """일정 이벤트 모델"""
    id: Optional[str] = None
    title: str = Field(..., description="이벤트 제목")
    description: Optional[str] = Field(None, description="이벤트 설명")
    start_time: datetime.datetime = Field(..., description="시작 시간")
    end_time: datetime.datetime = Field(..., description="종료 시간")
    location: Optional[str] = Field(None, description="장소")
    participants: Optional[List[str]] = Field(None, description="참가자")
    priority: Optional[int] = Field(1, description="우선순위, 1-5, 5가 최고")
    status: Optional[str] = Field("pending", description="상태: pending, completed, cancelled")
    reminder: Optional[bool] = Field(False, description="알림 설정 여부")
    reminder_time: Optional[datetime.datetime] = Field(None, description="알림 시간")
    recurring: Optional[bool] = Field(False, description="반복 여부")
    recurring_pattern: Optional[str] = Field(None, description="반복 패턴, 예: daily, weekly, monthly")

class ScheduleAgent:
    """일정 관리 지능형 에이전트, 사용자의 일정 관련 요청 처리"""
    
    def __init__(self, llm=None):
        """일정 관리 지능형 에이전트 초기화
        
        Args:
            llm: 언어 모델, 기본값으로 Google Gemini 모델 사용
        """
        self.llm = llm or ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-preview-04-17",
            temperature=0.2,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        self.agent = self._create_agent()
        
        # 데이터 디렉토리 존재 확인
        CSVDatabase.ensure_data_dir()
        
    def _create_agent(self) -> Agent:
        """CrewAI Agent 생성"""
        
        # Agent의 도구 정의
        tools = [
            Tool(
                name="create_schedule",
                func=self.create_schedule,
                description="새로운 일정 안배 생성"
            ),
            Tool(
                name="update_schedule",
                func=self.update_schedule,
                description="기존 일정 안배 업데이트"
            ),
            Tool(
                name="delete_schedule",
                func=self.delete_schedule,
                description="일정 안배 삭제"
            ),
            Tool(
                name="get_schedule",
                func=self.get_schedule,
                description="특정 일정 안배의 상세 정보 가져오기"
            ),
            Tool(
                name="list_schedules",
                func=self.list_schedules,
                description="특정 시간대 내의 모든 일정 안배 나열"
            ),
            Tool(
                name="recommend_schedule",
                func=self.recommend_schedule,
                description="사용자 습관과 기존 일정에 따라 최적의 안배 시간 추천"
            ),
            Tool(
                name="check_conflicts",
                func=self.check_conflicts,
                description="일정 안배의 충돌 여부 확인"
            ),
            Tool(
                name="set_reminder",
                func=self.set_reminder,
                description="일정 안배에 알림 설정"
            ),
        ]
        
        # Agent 정의
        schedule_agent = Agent(
            role="일정 관리 전문가",
            goal="사용자가 효율적으로 일정을 관리할 수 있도록 도와주고, 지능형 일정 제안을 제공하며, 충돌을 방지하고, 중요한 사항이 적절히 안배되도록 보장",
            backstory="""
            당신은 경험이 풍부한 일정 관리 전문가로, 사용자가 시간 안배를 조직하고 최적화하는 데 능숙합니다.
            다양한 유형의 활동 우선순위를 이해하고, 사용자의 습관과 선호도에 따라 개인화된 일정 제안을 제공할 수 있습니다.
            사용자의 작업 모드, 휴식 필요 및 개인 습관을 고려하여 일정 안배가 효율적이면서도 인간적이 되도록 보장합니다.
            잠재적인 일정 충돌을 발견하고 합리적인 해결책을 제공하는 데 능숙합니다.
            """,
            verbose=True,
            llm=self.llm,
            tools=tools
        )
        
        return schedule_agent
    
    async def process_request(self, user_id: str, request: str) -> Dict[str, Any]:
        """사용자의 일정 관련 요청 처리
        
        Args:
            user_id: 사용자 ID
            request: 사용자 요청 내용
            
        Returns:
            처리 결과
        """
        # 작업 생성
        task = Task(
            description=f"사용자의 일정 요청 처리: {request}",
            agent=self.agent,
            context={
                "user_id": user_id,
                "request": request,
                "current_time": datetime.datetime.now().isoformat()
            }
        )
        
        # Crew 생성 및 작업 실행
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            verbose=True
        )
        
        result = await crew.kickoff()
        return {"response": result}
    
    # 도구 메서드 구현
    async def create_schedule(self, user_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """새로운 일정 안배 생성
        
        Args:
            user_id: 사용자 ID
            event: 일정 이벤트 데이터
            
        Returns:
            생성된 일정 이벤트
        """
        try:
            # 일정 이벤트 생성
            schedule_event = ScheduleEvent(**event)
            
            # CSV 데이터베이스에 저장
            created_event = await ScheduleCSV.create_schedule(user_id, schedule_event.dict(exclude_none=True))
            
            return {
                "status": "success",
                "message": "일정 생성 성공",
                "data": created_event
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"일정 생성 실패: {str(e)}",
                "data": None
            }
    
    async def update_schedule(self, user_id: str, event_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """기존 일정 안배 업데이트
        
        Args:
            user_id: 사용자 ID
            event_id: 일정 이벤트 ID
            updates: 업데이트할 필드
            
        Returns:
            업데이트된 일정 이벤트
        """
        try:
            # 일정 업데이트
            updated_event = await ScheduleCSV.update_schedule(user_id, event_id, updates)
            
            if not updated_event:
                return {
                    "status": "error",
                    "message": "일정이 존재하지 않거나 업데이트 권한이 없습니다",
                    "data": None
                }
            
            return {
                "status": "success",
                "message": "일정 업데이트 성공",
                "data": updated_event
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"일정 업데이트 실패: {str(e)}",
                "data": None
            }
    
    async def delete_schedule(self, user_id: str, event_id: str) -> Dict[str, Any]:
        """일정 안배 삭제
        
        Args:
            user_id: 사용자 ID
            event_id: 일정 이벤트 ID
            
        Returns:
            삭제 결과
        """
        try:
            # 일정 삭제
            success = await ScheduleCSV.delete_schedule(user_id, event_id)
            
            if not success:
                return {
                    "status": "error",
                    "message": "일정이 존재하지 않거나 삭제 권한이 없습니다",
                    "data": None
                }
            
            return {
                "status": "success",
                "message": "일정 삭제 성공",
                "data": {"id": event_id}
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"일정 삭제 실패: {str(e)}",
                "data": None
            }
    
    async def get_schedule(self, user_id: str, event_id: str) -> Dict[str, Any]:
        """특정 일정 안배의 상세 정보 가져오기
        
        Args:
            user_id: 사용자 ID
            event_id: 일정 이벤트 ID
            
        Returns:
            일정 이벤트 상세 정보
        """
        try:
            # 일정 가져오기
            event = await ScheduleCSV.get_schedule(user_id, event_id)
            
            if not event:
                return {
                    "status": "error",
                    "message": "일정이 존재하지 않거나 조회 권한이 없습니다",
                    "data": None
                }
            
            return {
                "status": "success",
                "message": "일정 가져오기 성공",
                "data": event
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"일정 가져오기 실패: {str(e)}",
                "data": None
            }
    
    async def list_schedules(self, user_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """특정 시간대 내의 모든 일정 안배 나열
        
        Args:
            user_id: 사용자 ID
            start_date: 시작 날짜
            end_date: 종료 날짜
            
        Returns:
            일정 이벤트 목록
        """
        try:
            # 일정 목록 가져오기
            events = await ScheduleCSV.list_schedules(user_id, start_date, end_date)
            
            return {
                "status": "success",
                "message": "일정 목록 가져오기 성공",
                "data": events
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"일정 목록 가져오기 실패: {str(e)}",
                "data": None
            }
    
    async def recommend_schedule(self, user_id: str, event_duration: int, preferred_date: str = None) -> Dict[str, Any]:
        """사용자 습관과 기존 일정에 따라 최적의 안배 시간 추천
        
        Args:
            user_id: 사용자 ID
            event_duration: 이벤트 지속 시간(분)
            preferred_date: 선호 날짜, 선택사항
            
        Returns:
            추천 시간대
        """
        try:
            # 조회할 시간 범위 결정
            now = ScheduleUtils.get_current_datetime()
            
            # 선호 날짜가 제공된 경우, 해당 날짜를 시작 날짜로 사용
            if preferred_date:
                start_date = ScheduleUtils.parse_datetime(preferred_date)
                # 시작 날짜가 현재 날짜보다 이르지 않도록 보장
                if start_date < now:
                    start_date = now
                end_date = start_date + datetime.timedelta(days=1)
            else:
                # 기본적으로 현재부터 향후 7일간의 일정 조회
                start_date = now
                end_date = now + datetime.timedelta(days=7)
            
            # 해당 시간대 내 사용자의 모든 일정 가져오기
            events = await ScheduleCSV.list_schedules(
                user_id, 
                start_date.isoformat(), 
                end_date.isoformat()
            )
            
            # 바쁜 시간대 목록으로 변환
            busy_periods = []
            for event in events:
                start_time = event["start_time"]
                end_time = event["end_time"]
                
                if isinstance(start_time, str):
                    start_time = ScheduleUtils.parse_datetime(start_time)
                if isinstance(end_time, str):
                    end_time = ScheduleUtils.parse_datetime(end_time)
                    
                busy_periods.append({"start": start_time, "end": end_time})
            
            # 여유 시간대 가져오기
            free_slots = ScheduleUtils.get_free_slots(
                busy_periods, 
                start_date, 
                end_date, 
                min_duration_minutes=event_duration
            )
            
            # 충분히 긴 여유 시간대가 없으면 검색 범위 확대
            if not free_slots:
                end_date = start_date + datetime.timedelta(days=14)
                events = await ScheduleCSV.list_schedules(
                    user_id, 
                    start_date.isoformat(), 
                    end_date.isoformat()
                )
                
                busy_periods = []
                for event in events:
                    start_time = event["start_time"]
                    end_time = event["end_time"]
                    
                    if isinstance(start_time, str):
                        start_time = ScheduleUtils.parse_datetime(start_time)
                    if isinstance(end_time, str):
                        end_time = ScheduleUtils.parse_datetime(end_time)
                        
                    busy_periods.append({"start": start_time, "end": end_time})
                
                free_slots = ScheduleUtils.get_free_slots(
                    busy_periods, 
                    start_date, 
                    end_date, 
                    min_duration_minutes=event_duration
                )
            
            # 여전히 적절한 시간대를 찾지 못하면 기본 추천 반환
            if not free_slots:
                recommended_time = start_date + datetime.timedelta(days=1, hours=10)
                return {
                    "status": "success",
                    "message": "일정 추천 성공",
                    "data": {
                        "recommended_start": recommended_time.isoformat(),
                        "recommended_end": (recommended_time + datetime.timedelta(minutes=event_duration)).isoformat(),
                        "reason": "완전히 여유로운 시간대를 찾지 못했습니다. 이것은 기본 추천입니다. 기존 일정을 조정해야 할 수도 있습니다."
                    }
                }
            
            # 최적의 여유 시간대 선택
            # 근무 시간 내 시간대 우선 선택
            work_hour_slots = [
                slot for slot in free_slots 
                if ScheduleUtils.is_working_hours(slot["start"]) and ScheduleUtils.is_working_hours(slot["end"])
            ]
            
            if work_hour_slots:
                best_slot = work_hour_slots[0]
            else:
                # 근무 시간 내 시간대가 없으면 첫 번째 여유 시간대 선택
                best_slot = free_slots[0]
            
            # 시간대가 너무 길지 않도록 보장(필요한 지속 시간만 사용)
            end_time = ScheduleUtils.add_minutes(best_slot["start"], event_duration)
            
            # 추천 이유 생성
            reason = "이 시간대는 일정이 없으며 필요한 기간을 충분히 충족합니다."
            if ScheduleUtils.is_working_hours(best_slot["start"]):
                reason += " 그리고 정규 근무 시간 내에 있습니다."
            
            return {
                "status": "success",
                "message": "일정 추천 성공",
                "data": {
                    "recommended_start": best_slot["start"].isoformat(),
                    "recommended_end": end_time.isoformat(),
                    "reason": reason
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"일정 추천 실패: {str(e)}",
                "data": None
            }
    
    async def check_conflicts(self, user_id: str, proposed_event: Dict[str, Any]) -> Dict[str, Any]:
        """일정 안배의 충돌 여부 확인
        
        Args:
            user_id: 사용자 ID
            proposed_event: 제안된 일정 이벤트 데이터
            
        Returns:
            충돌 확인 결과
        """
        try:
            # 제안된 일정의 시간 가져오기
            start_time = proposed_event.get("start_time")
            end_time = proposed_event.get("end_time")
            
            if not start_time or not end_time:
                return {
                    "status": "error",
                    "message": "시작 시간과 종료 시간이 필요합니다",
                    "data": None
                }
            
            # 문자열이면 datetime으로 변환
            if isinstance(start_time, str):
                start_time = ScheduleUtils.parse_datetime(start_time)
            if isinstance(end_time, str):
                end_time = ScheduleUtils.parse_datetime(end_time)
                
            # 해당 시간대의 일정 가져오기
            events = await ScheduleCSV.list_schedules(
                user_id,
                start_time.isoformat(),
                end_time.isoformat()
            )
            
            # 충돌 확인
            conflicts = []
            for event in events:
                event_start = event["start_time"]
                event_end = event["end_time"]
                
                if isinstance(event_start, str):
                    event_start = ScheduleUtils.parse_datetime(event_start)
                if isinstance(event_end, str):
                    event_end = ScheduleUtils.parse_datetime(event_end)
                
                # 시간대 격자 확인
                if ScheduleUtils.check_overlap(start_time, end_time, event_start, event_end):
                    conflicts.append(event)
            
            return {
                "status": "success",
                "message": "충돌 확인 완료",
                "data": {
                    "has_conflicts": len(conflicts) > 0,
                    "conflicts": conflicts
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"충돌 확인 실패: {str(e)}",
                "data": None
            }
    
    async def set_reminder(self, user_id: str, event_id: str, reminder_time: str = None) -> Dict[str, Any]:
        """일정 안배에 알림 설정
        
        Args:
            user_id: 사용자 ID
            event_id: 일정 이벤트 ID
            reminder_time: 알림 시간, 선택사항. 제공되지 않으면 이벤트 시작 30분 전으로 설정
            
        Returns:
            알림 설정 결과
        """
        try:
            # 일정 가져오기
            event = await ScheduleCSV.get_schedule(user_id, event_id)
            
            if not event:
                return {
                    "status": "error",
                    "message": "일정이 존재하지 않거나 조회 권한이 없습니다",
                    "data": None
                }
            
            # 알림 시간 처리
            if reminder_time:
                reminder_datetime = ScheduleUtils.parse_datetime(reminder_time)
            else:
                # 기본값: 이벤트 시작 30분 전
                event_start = event["start_time"]
                if isinstance(event_start, str):
                    event_start = ScheduleUtils.parse_datetime(event_start)
                reminder_datetime = event_start - datetime.timedelta(minutes=30)
            
            # 일정 업데이트
            updates = {
                "reminder": True,
                "reminder_time": reminder_datetime.isoformat()
            }
            
            updated_event = await ScheduleCSV.update_schedule(user_id, event_id, updates)
            
            return {
                "status": "success",
                "message": "알림 설정 성공",
                "data": updated_event
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"알림 설정 실패: {str(e)}",
                "data": None
            }
