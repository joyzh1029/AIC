import asyncio
import json
import datetime
from agents.schedule_agent import ScheduleAgent
from utils.schedule_utils import ScheduleUtils

async def test_schedule_agent():
    """일정 관리 Agent의 각종 기능 테스트"""
    # 일정 관리 Agent 초기화
    agent = ScheduleAgent()
    
    # 테스트 사용자 ID
    user_id = "test_user"
    
    print("===== 일정 관리 Agent 테스트 =====")
    
    # 1. 일정 생성 테스트
    print("\n1. 일정 생성 테스트")
    create_result = await agent.create_schedule(user_id, {
        "title": "테스트 회의",
        "description": "일정 관리 Agent 테스트",
        "start_time": datetime.datetime.now() + datetime.timedelta(days=1, hours=10),
        "end_time": datetime.datetime.now() + datetime.timedelta(days=1, hours=11),
        "location": "회의실",
        "participants": ["홍길동", "김철수"],
        "priority": 3
    })
    print(f"일정 생성 결과: {json.dumps(create_result, indent=2, ensure_ascii=False)}")
    
    # 생성된 일정 ID 가져오기
    if create_result["status"] == "success":
        schedule_id = create_result["data"]["id"]
        
        # 2. 일정 상세 정보 가져오기 테스트
        print("\n2. 일정 상세 정보 가져오기 테스트")
        get_result = await agent.get_schedule(user_id, schedule_id)
        print(f"일정 상세 정보 가져오기 결과: {json.dumps(get_result, indent=2, ensure_ascii=False)}")
        
        # 3. 일정 업데이트 테스트
        print("\n3. 일정 업데이트 테스트")
        update_result = await agent.update_schedule(user_id, schedule_id, {
            "title": "업데이트된 테스트 회의",
            "priority": 4
        })
        print(f"일정 업데이트 결과: {json.dumps(update_result, indent=2, ensure_ascii=False)}")
        
        # 4. 알림 설정 테스트
        print("\n4. 알림 설정 테스트")
        reminder_time = (datetime.datetime.now() + datetime.timedelta(days=1, hours=9, minutes=30)).isoformat()
        reminder_result = await agent.set_reminder(user_id, schedule_id, reminder_time)
        print(f"알림 설정 결과: {json.dumps(reminder_result, indent=2, ensure_ascii=False)}")
    
    # 5. 일정 목록 테스트
    print("\n5. 일정 목록 테스트")
    start_date = datetime.datetime.now().isoformat()
    end_date = (datetime.datetime.now() + datetime.timedelta(days=7)).isoformat()
    list_result = await agent.list_schedules(user_id, start_date, end_date)
    print(f"일정 목록 결과: {json.dumps(list_result, indent=2, ensure_ascii=False)}")
    
    # 6. 충돌 확인 테스트
    print("\n6. 충돌 확인 테스트")
    conflict_check_result = await agent.check_conflicts(user_id, {
        "start_time": datetime.datetime.now() + datetime.timedelta(days=1, hours=10, minutes=30),
        "end_time": datetime.datetime.now() + datetime.timedelta(days=1, hours=11, minutes=30)
    })
    print(f"충돌 확인 결과: {json.dumps(conflict_check_result, indent=2, ensure_ascii=False)}")
    
    # 7. 시간 추천 테스트
    print("\n7. 시간 추천 테스트")
    recommend_result = await agent.recommend_schedule(user_id, 60)  # 60분 시간대 추천
    print(f"시간 추천 결과: {json.dumps(recommend_result, indent=2, ensure_ascii=False)}")
    
    # 8. 일정 삭제 테스트
    if create_result["status"] == "success":
        print("\n8. 일정 삭제 테스트")
        delete_result = await agent.delete_schedule(user_id, schedule_id)
        print(f"일정 삭제 결과: {json.dumps(delete_result, indent=2, ensure_ascii=False)}")
    
    print("\n===== 테스트 완료 =====")

if __name__ == "__main__":
    asyncio.run(test_schedule_agent())
