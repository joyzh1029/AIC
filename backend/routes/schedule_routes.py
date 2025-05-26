from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Dict, Any, List, Optional
import datetime
from pydantic import BaseModel, Field

from agents.schedule_agent import ScheduleAgent, ScheduleEvent

# FastAPI의 APIRouter를 사용하여 라우트 관리
# prefix, tags 등은 main.py에서 설정
router = APIRouter()
schedule_agent = ScheduleAgent()

class ScheduleRequest(BaseModel):
    """일정 요청 모델"""
    request: str = Field(..., description="사용자의 일정 요청 내용")

class CreateScheduleRequest(BaseModel):
    """일정 생성 요청 모델"""
    title: str = Field(..., description="일정 제목")
    description: Optional[str] = Field(None, description="일정 설명")
    start_time: datetime.datetime = Field(..., description="시작 시간")
    end_time: datetime.datetime = Field(..., description="종료 시간")
    location: Optional[str] = Field(None, description="장소")
    participants: Optional[List[str]] = Field(None, description="참가자")
    priority: Optional[int] = Field(1, description="우선순위, 1-5, 5가 가장 높음")
    reminder: Optional[bool] = Field(False, description="알림 설정 여부")
    reminder_time: Optional[datetime.datetime] = Field(None, description="알림 시간")
    recurring: Optional[bool] = Field(False, description="반복 여부")
    recurring_pattern: Optional[str] = Field(None, description="반복 패턴, 예: daily, weekly, monthly")

class UpdateScheduleRequest(BaseModel):
    """일정 업데이트 요청 모델"""
    title: Optional[str] = Field(None, description="일정 제목")
    description: Optional[str] = Field(None, description="일정 설명")
    start_time: Optional[datetime.datetime] = Field(None, description="시작 시간")
    end_time: Optional[datetime.datetime] = Field(None, description="종료 시간")
    location: Optional[str] = Field(None, description="장소")
    participants: Optional[List[str]] = Field(None, description="참가자")
    priority: Optional[int] = Field(None, description="우선순위, 1-5, 5가 가장 높음")
    status: Optional[str] = Field(None, description="상태: pending, completed, cancelled")
    reminder: Optional[bool] = Field(None, description="알림 설정 여부")
    reminder_time: Optional[datetime.datetime] = Field(None, description="알림 시간")
    recurring: Optional[bool] = Field(None, description="반복 여부")
    recurring_pattern: Optional[str] = Field(None, description="반복 패턴, 예: daily, weekly, monthly")

@router.post("/process")
async def process_schedule_request(
    user_id: str, 
    request: ScheduleRequest = Body(...)
) -> Dict[str, Any]:
    """사용자의 일정 관련 자연어 요청 처리
    
    이 엔드포인트는 사용자의 자연어 요청을 받아 ScheduleAgent를 사용하여 처리합니다
    """
    try:
        result = await schedule_agent.process_request(user_id, request.request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일정 요청 처리 실패: {str(e)}"
        )

@router.post("/events")
async def create_schedule_event(
    user_id: str,
    event: CreateScheduleRequest = Body(...)
) -> Dict[str, Any]:
    """새 일정 이벤트 생성"""
    try:
        result = await schedule_agent.create_schedule(user_id, event.dict(exclude_none=True))
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일정 생성 실패: {str(e)}"
        )

@router.put("/events/{event_id}")
async def update_schedule_event(
    user_id: str,
    event_id: str,
    updates: UpdateScheduleRequest = Body(...)
) -> Dict[str, Any]:
    """기존 일정 이벤트 업데이트"""
    try:
        result = await schedule_agent.update_schedule(
            user_id, 
            event_id, 
            updates.dict(exclude_none=True)
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일정 업데이트 실패: {str(e)}"
        )

@router.delete("/events/{event_id}")
async def delete_schedule_event(
    user_id: str,
    event_id: str
) -> Dict[str, Any]:
    """일정 이벤트 삭제"""
    try:
        result = await schedule_agent.delete_schedule(user_id, event_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일정 삭제 실패: {str(e)}"
        )

@router.get("/events/{event_id}")
async def get_schedule_event(
    user_id: str,
    event_id: str
) -> Dict[str, Any]:
    """특정 일정 이벤트의 상세 정보 조회"""
    try:
        result = await schedule_agent.get_schedule(user_id, event_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일정 조회 실패: {str(e)}"
        )

@router.get("/events")
async def list_schedule_events(
    user_id: str,
    start_date: str,
    end_date: str
) -> Dict[str, Any]:
    """특정 기간 내의 모든 일정 이벤트 나열"""
    try:
        result = await schedule_agent.list_schedules(user_id, start_date, end_date)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일정 목록 조회 실패: {str(e)}"
        )

@router.post("/recommend")
async def recommend_schedule_time(
    user_id: str,
    event_duration: int,
    preferred_date: Optional[str] = None
) -> Dict[str, Any]:
    """최적의 일정 시간 추천"""
    try:
        result = await schedule_agent.recommend_schedule(
            user_id, 
            event_duration, 
            preferred_date
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일정 추천 실패: {str(e)}"
        )

@router.post("/check-conflicts")
async def check_schedule_conflicts(
    user_id: str,
    proposed_event: CreateScheduleRequest = Body(...)
) -> Dict[str, Any]:
    """일정 충돌 여부 확인"""
    try:
        result = await schedule_agent.check_conflicts(
            user_id, 
            proposed_event.dict(exclude_none=True)
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"충돌 확인 실패: {str(e)}"
        )

@router.post("/events/{event_id}/reminder")
async def set_schedule_reminder(
    user_id: str,
    event_id: str,
    reminder_time: str = Body(...)
) -> Dict[str, Any]:
    """일정 이벤트에 알림 설정"""
    try:
        result = await schedule_agent.set_reminder(user_id, event_id, reminder_time)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"알림 설정 실패: {str(e)}"
        )
