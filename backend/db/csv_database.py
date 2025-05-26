import csv
import os
import datetime
import uuid
from typing import List, Dict, Any, Optional
import pandas as pd
from utils.schedule_utils import ScheduleUtils

class CSVDatabase:
    """CSV 파일 데이터베이스 조작 클래스"""
    
    # 데이터 파일 경로
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    
    @classmethod
    def ensure_data_dir(cls):
        """데이터 디렉토리 존재 확인"""
        if not os.path.exists(cls.DATA_DIR):
            os.makedirs(cls.DATA_DIR)
    
    @classmethod
    def get_user_schedule_file(cls, user_id: str) -> str:
        """사용자 일정 파일 경로 가져오기"""
        cls.ensure_data_dir()
        return os.path.join(cls.DATA_DIR, f"schedule_{user_id}.csv")
    
    @classmethod
    def file_exists(cls, file_path: str) -> bool:
        """파일 존재 여부 확인"""
        return os.path.exists(file_path)
    
    @classmethod
    def create_schedule_file(cls, file_path: str):
        """일정 파일 생성"""
        # CSV 파일의 열 정의
        columns = [
            "id", "user_id", "title", "description", "start_time", "end_time",
            "location", "participants", "priority", "status", "reminder",
            "reminder_time", "recurring", "recurring_pattern", "created_at", "updated_at"
        ]
        
        # CSV 파일 생성
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)

class ScheduleCSV:
    """일정 CSV 데이터 조작 클래스"""
    
    @classmethod
    async def create_schedule(cls, user_id: str, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """새로운 일정 생성"""
        # 사용자 일정 파일 경로 가져오기
        file_path = CSVDatabase.get_user_schedule_file(user_id)
        
        # 파일이 존재하지 않으면 파일 생성
        if not CSVDatabase.file_exists(file_path):
            CSVDatabase.create_schedule_file(file_path)
        
        # 고유 ID 생성
        schedule_id = str(uuid.uuid4())
        
        # 필수 필드 추가
        now = datetime.datetime.now().isoformat()
        schedule_data.update({
            "id": schedule_id,
            "user_id": user_id,
            "created_at": now,
            "updated_at": now
        })
        
        # participants 필드 처리 (존재하는 경우)
        if "participants" in schedule_data and isinstance(schedule_data["participants"], list):
            schedule_data["participants"] = ",".join(schedule_data["participants"])
        
        # 기존 데이터 읽기
        try:
            df = pd.read_csv(file_path)
        except pd.errors.EmptyDataError:
            # 파일이 비어있으면 빈 DataFrame 생성
            columns = [
                "id", "user_id", "title", "description", "start_time", "end_time",
                "location", "participants", "priority", "status", "reminder",
                "reminder_time", "recurring", "recurring_pattern", "created_at", "updated_at"
            ]
            df = pd.DataFrame(columns=columns)
        
        # 새 데이터 추가
        df = pd.concat([df, pd.DataFrame([schedule_data])], ignore_index=True)
        
        # 데이터 저장
        df.to_csv(file_path, index=False)
        
        # 생성된 일정 반환
        return schedule_data
    
    @classmethod
    async def update_schedule(cls, user_id: str, schedule_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """일정 업데이트"""
        # 사용자 일정 파일 경로 가져오기
        file_path = CSVDatabase.get_user_schedule_file(user_id)
        
        # 파일이 존재하지 않으면 None 반환
        if not CSVDatabase.file_exists(file_path):
            return None
        
        # 데이터 읽기
        df = pd.read_csv(file_path)
        
        # 지정된 ID의 일정 찾기
        mask = (df["id"] == schedule_id) & (df["user_id"] == user_id)
        if not mask.any():
            return None
        
        # participants 필드 처리 (존재하는 경우)
        if "participants" in updates and isinstance(updates["participants"], list):
            updates["participants"] = ",".join(updates["participants"])
        
        # 데이터 업데이트
        updates["updated_at"] = datetime.datetime.now().isoformat()
        for key, value in updates.items():
            df.loc[mask, key] = value
        
        # 데이터 저장
        df.to_csv(file_path, index=False)
        
        # 업데이트된 일정 반환
        updated_schedule = df[mask].to_dict("records")[0]
        
        # participants 필드 처리 (존재하는 경우)
        if "participants" in updated_schedule and isinstance(updated_schedule["participants"], str) and updated_schedule["participants"]:
            updated_schedule["participants"] = updated_schedule["participants"].split(",")
        
        return updated_schedule
    
    @classmethod
    async def delete_schedule(cls, user_id: str, schedule_id: str) -> bool:
        """일정 삭제"""
        # 사용자 일정 파일 경로 가져오기
        file_path = CSVDatabase.get_user_schedule_file(user_id)
        
        # 파일이 존재하지 않으면 False 반환
        if not CSVDatabase.file_exists(file_path):
            return False
        
        # 데이터 읽기
        df = pd.read_csv(file_path)
        
        # 지정된 ID의 일정 찾기
        mask = (df["id"] == schedule_id) & (df["user_id"] == user_id)
        if not mask.any():
            return False
        
        # 데이터 삭제
        df = df[~mask]
        
        # 데이터 저장
        df.to_csv(file_path, index=False)
        
        return True
    
    @classmethod
    async def get_schedule(cls, user_id: str, schedule_id: str) -> Dict[str, Any]:
        """특정 일정 가져오기"""
        # 사용자 일정 파일 경로 가져오기
        file_path = CSVDatabase.get_user_schedule_file(user_id)
        
        # 파일이 존재하지 않으면 None 반환
        if not CSVDatabase.file_exists(file_path):
            return None
        
        # 데이터 읽기
        df = pd.read_csv(file_path)
        
        # 지정된 ID의 일정 찾기
        mask = (df["id"] == schedule_id) & (df["user_id"] == user_id)
        if not mask.any():
            return None
        
        # 일정 데이터 가져오기
        schedule = df[mask].to_dict("records")[0]
        
        # participants 필드 처리 (존재하는 경우)
        if "participants" in schedule and isinstance(schedule["participants"], str) and schedule["participants"]:
            schedule["participants"] = schedule["participants"].split(",")
        
        return schedule
    
    @classmethod
    async def list_schedules(cls, user_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """특정 시간대 내의 모든 일정 나열"""
        # 사용자 일정 파일 경로 가져오기
        file_path = CSVDatabase.get_user_schedule_file(user_id)
        
        # 파일이 존재하지 않으면 빈 목록 반환
        if not CSVDatabase.file_exists(file_path):
            return []
        
        # 데이터 읽기
        df = pd.read_csv(file_path)
        
        # 사용자 ID 필터링
        df = df[df["user_id"] == user_id]
        
        # 데이터가 없으면 빈 목록 반환
        if df.empty:
            return []
        
        # 시간 범위 필터링
        # 참고: 여기서는 start_time과 end_time이 ISO 형식의 문자열이라고 가정
        mask = (
            (df["start_time"] >= start_date) & 
            (df["end_time"] <= end_date)
        )
        df = df[mask]
        
        # 데이터가 없으면 빈 목록 반환
        if df.empty:
            return []
        
        # 시작 시간으로 정렬
        df = df.sort_values("start_time")
        
        # 딕셔너리 목록으로 변환
        schedules = df.to_dict("records")
        
        # participants 필드 처리
        for schedule in schedules:
            if "participants" in schedule and isinstance(schedule["participants"], str) and schedule["participants"]:
                schedule["participants"] = schedule["participants"].split(",")
        
        return schedules
    
    @classmethod
    async def find_conflicting_schedules(cls, user_id: str, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """주어진 시간대와 충돌하는 일정 찾기"""
        # 사용자 일정 파일 경로 가져오기
        file_path = CSVDatabase.get_user_schedule_file(user_id)
        
        # 파일이 존재하지 않으면 빈 목록 반환
        if not CSVDatabase.file_exists(file_path):
            return []
        
        # 데이터 읽기
        df = pd.read_csv(file_path)
        
        # 사용자 ID 필터링
        df = df[df["user_id"] == user_id]
        
        # 데이터가 없으면 빈 목록 반환
        if df.empty:
            return []
        
        # 충돌하는 일정 찾기
        # 충돌 조건:
        # 1. 시작 시간이 목표 시간대 내에 있음
        # 2. 종료 시간이 목표 시간대 내에 있음
        # 3. 목표 시간대가 일정 시간 내에 완전히 포함됨
        mask = (
            ((df["start_time"] >= start_time) & (df["start_time"] < end_time)) |
            ((df["end_time"] > start_time) & (df["end_time"] <= end_time)) |
            ((df["start_time"] <= start_time) & (df["end_time"] >= end_time))
        )
        df = df[mask]
        
        # 데이터가 없으면 빈 목록 반환
        if df.empty:
            return []
        
        # 딕셔너리 목록으로 변환
        conflicts = df.to_dict("records")
        
        # participants 필드 처리
        for conflict in conflicts:
            if "participants" in conflict and isinstance(conflict["participants"], str) and conflict["participants"]:
                conflict["participants"] = conflict["participants"].split(",")
        
        return conflicts
