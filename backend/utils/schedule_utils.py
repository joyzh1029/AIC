import datetime
from typing import List, Dict, Any, Optional
import pytz

class ScheduleUtils:
    """일정 관리 유틸리티 클래스"""
    
    @staticmethod
    def parse_datetime(date_str: str) -> datetime.datetime:
        """날짜 시간 문자열을 datetime 객체로 파싱
        
        다양한 형식 지원:
        - ISO 형식: 2025-05-26T10:30:00
        - 날짜: 2025-05-26
        - 날짜 시간: 2025-05-26 10:30:00
        """
        try:
            # ISO 형식 파싱 시도
            return datetime.datetime.fromisoformat(date_str)
        except ValueError:
            pass
        
        # 다른 형식 파싱 시도
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d",
            "%Y/%m/%d %H:%M:%S",
            "%d/%m/%Y",
            "%d/%m/%Y %H:%M:%S"
        ]
        
        for fmt in formats:
            try:
                return datetime.datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"날짜 시간을 파싱할 수 없습니다: {date_str}")
    
    @staticmethod
    def format_datetime(dt: datetime.datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """datetime 객체를 문자열로 포맷"""
        return dt.strftime(fmt)
    
    @staticmethod
    def get_current_datetime(timezone: str = "Asia/Seoul") -> datetime.datetime:
        """현재 시간 가져오기, 기본값은 한국 시간대"""
        tz = pytz.timezone(timezone)
        return datetime.datetime.now(tz)
    
    @staticmethod
    def check_overlap(start1: datetime.datetime, end1: datetime.datetime, 
                      start2: datetime.datetime, end2: datetime.datetime) -> bool:
        """두 시간대가 겹치는지 확인"""
        return max(start1, start2) < min(end1, end2)
    
    @staticmethod
    def calculate_duration(start: datetime.datetime, end: datetime.datetime) -> int:
        """두 시간점 사이의 분 수 계산"""
        delta = end - start
        return int(delta.total_seconds() / 60)
    
    @staticmethod
    def add_minutes(dt: datetime.datetime, minutes: int) -> datetime.datetime:
        """datetime에 분 수 추가"""
        return dt + datetime.timedelta(minutes=minutes)
    
    @staticmethod
    def get_next_occurrence(base_date: datetime.datetime, pattern: str) -> datetime.datetime:
        """반복 패턴에 따라 다음 발생 날짜 시간 가져오기
        
        Args:
            base_date: 기준 날짜 시간
            pattern: 반복 패턴, 예: daily, weekly, monthly, yearly
            
        Returns:
            다음 발생 날짜 시간
        """
        if pattern == "daily":
            return base_date + datetime.timedelta(days=1)
        elif pattern == "weekly":
            return base_date + datetime.timedelta(days=7)
        elif pattern == "biweekly":
            return base_date + datetime.timedelta(days=14)
        elif pattern == "monthly":
            # 간단한 처리, 월말 날짜 문제 고려하지 않음
            new_month = base_date.month + 1
            new_year = base_date.year
            if new_month > 12:
                new_month = 1
                new_year += 1
            
            day = min(base_date.day, [31, 29 if ScheduleUtils.is_leap_year(new_year) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][new_month-1])
            
            return base_date.replace(year=new_year, month=new_month, day=day)
        elif pattern == "yearly":
            return base_date.replace(year=base_date.year + 1)
        else:
            raise ValueError(f"지원하지 않는 반복 패턴: {pattern}")
    
    @staticmethod
    def is_leap_year(year: int) -> bool:
        """윤년인지 판단"""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    
    @staticmethod
    def get_time_of_day(dt: datetime.datetime) -> str:
        """하루 중 시간대 가져오기
        
        Returns:
            시간대: morning, afternoon, evening, night
        """
        hour = dt.hour
        
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    @staticmethod
    def is_weekend(dt: datetime.datetime) -> bool:
        """주말인지 판단"""
        return dt.weekday() >= 5  # 5와 6은 각각 토요일과 일요일
    
    @staticmethod
    def is_working_hours(dt: datetime.datetime) -> bool:
        """근무 시간인지 판단 (월요일부터 금요일 9:00-18:00)"""
        if ScheduleUtils.is_weekend(dt):
            return False
        
        return 9 <= dt.hour < 18
    
    @staticmethod
    def get_free_slots(busy_periods: List[Dict[str, datetime.datetime]], 
                       start_date: datetime.datetime, 
                       end_date: datetime.datetime,
                       min_duration_minutes: int = 30) -> List[Dict[str, datetime.datetime]]:
        """바쁜 시간대에 따라 여유 시간대 계산
        
        Args:
            busy_periods: 바쁜 시간대 목록, 각 요소는 start와 end 포함
            start_date: 시작 날짜 시간
            end_date: 종료 날짜 시간
            min_duration_minutes: 최소 여유 시간대 지속 시간(분)
            
        Returns:
            여유 시간대 목록, 각 요소는 start와 end 포함
        """
        # 시작 시간으로 바쁜 시간대 정렬
        sorted_busy = sorted(busy_periods, key=lambda x: x["start"])
        
        free_slots = []
        current = start_date
        
        for busy in sorted_busy:
            busy_start = busy["start"]
            busy_end = busy["end"]
            
            # 현재 시간이 바쁜 시작 시간 이전이고, 간격이 충분히 긴 경우
            if current < busy_start and ScheduleUtils.calculate_duration(current, busy_start) >= min_duration_minutes:
                free_slots.append({"start": current, "end": busy_start})
            
            # 현재 시간을 바쁜 종료 시간으로 업데이트 (현재 시간이 바쁜 종료 시간보다 이른 경우)
            if current < busy_end:
                current = busy_end
        
        # 마지막 바쁜 시간대 이후부터 종료 날짜까지의 시간 확인
        if current < end_date and ScheduleUtils.calculate_duration(current, end_date) >= min_duration_minutes:
            free_slots.append({"start": current, "end": end_date})
        
        return free_slots
