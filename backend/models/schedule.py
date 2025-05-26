from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

class ScheduleEvent(BaseModel):
    """日程事件模型"""
    id: Optional[str] = None
    title: str = Field(..., description="事件标题")
    description: Optional[str] = Field(None, description="事件描述")
    start_time: datetime.datetime = Field(..., description="开始时间")
    end_time: datetime.datetime = Field(..., description="结束时间")
    location: Optional[str] = Field(None, description="地点")
    participants: Optional[List[str]] = Field(None, description="参与者")
    priority: Optional[int] = Field(1, description="优先级，1-5，5为最高")
    status: Optional[str] = Field("pending", description="状态：pending, completed, cancelled")
    reminder: Optional[bool] = Field(False, description="是否设置提醒")
    reminder_time: Optional[datetime.datetime] = Field(None, description="提醒时间")
    recurring: Optional[bool] = Field(False, description="是否重复")
    recurring_pattern: Optional[str] = Field(None, description="重复模式，如daily, weekly, monthly")
    user_id: str = Field(..., description="用户ID")
    
    class Config:
        schema_extra = {
            "example": {
                "title": "项目会议",
                "description": "讨论AIC项目进度",
                "start_time": "2025-05-27T10:00:00",
                "end_time": "2025-05-27T11:30:00",
                "location": "线上会议",
                "participants": ["张三", "李四"],
                "priority": 4,
                "status": "pending",
                "reminder": True,
                "reminder_time": "2025-05-27T09:45:00",
                "recurring": False,
                "user_id": "user123"
            }
        }
