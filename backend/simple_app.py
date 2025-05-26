from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from datetime import datetime

# 创建FastAPI应用
app = FastAPI(title="AIC Backend API (Simple)", description="Simple version of AI Companion Backend API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 示例数据
schedules = [
    {
        "id": "1",
        "title": "会议",
        "description": "团队周会",
        "start_time": "2025-05-26T10:00:00",
        "end_time": "2025-05-26T11:00:00",
        "location": "会议室A",
        "participants": ["张三", "李四", "王五"],
        "priority": 3
    },
    {
        "id": "2",
        "title": "午餐",
        "description": "与客户共进午餐",
        "start_time": "2025-05-26T12:00:00",
        "end_time": "2025-05-26T13:30:00",
        "location": "餐厅",
        "participants": ["张三", "客户"],
        "priority": 2
    }
]

@app.get("/")
async def root():
    return {"message": "Welcome to AIC Backend API (Simple Version)"}

@app.get("/api/schedule/list")
async def list_schedules():
    return {
        "status": "success",
        "message": "获取日程列表成功",
        "data": schedules
    }

@app.get("/api/schedule/{schedule_id}")
async def get_schedule(schedule_id: str):
    for schedule in schedules:
        if schedule["id"] == schedule_id:
            return {
                "status": "success",
                "message": "获取日程详情成功",
                "data": schedule
            }
    return {
        "status": "error",
        "message": "日程不存在",
        "data": None
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "success",
        "message": "服务正常运行",
        "time": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # 确保端口可以从环境变量中获取（用于部署）
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("simple_app:app", host="127.0.0.1", port=port, reload=True)
