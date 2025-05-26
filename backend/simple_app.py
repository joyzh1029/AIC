from fastapi import FastAPI, HTTPException, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from datetime import datetime, timedelta
import pandas as pd
import uuid
import asyncio
from typing import List, Dict, Any, Optional

# 导入CSV数据库类
from db.csv_database import CSVDatabase, ScheduleCSV

# 创建FastAPI应用
app = FastAPI(title="AIC Backend API (Simple)", description="Simple version of AI Companion Backend API using CSV files")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保数据目录存在
CSVDatabase.ensure_data_dir()

# 默认用户ID
DEFAULT_USER_ID = "user123"

# 创建示例数据（如果不存在）
async def create_sample_data():
    # 检查用户的日程文件是否存在
    file_path = CSVDatabase.get_user_schedule_file(DEFAULT_USER_ID)
    
    if not CSVDatabase.file_exists(file_path):
        # 创建示例数据
        sample_schedules = [
            {
                "title": "会议",
                "description": "团队周会",
                "start_time": (datetime.now() + timedelta(days=1, hours=10)).isoformat(),
                "end_time": (datetime.now() + timedelta(days=1, hours=11)).isoformat(),
                "location": "会议室A",
                "participants": ["张三", "李四", "王五"],
                "priority": 3
            },
            {
                "title": "午餐",
                "description": "与客户共进午餐",
                "start_time": (datetime.now() + timedelta(days=1, hours=12)).isoformat(),
                "end_time": (datetime.now() + timedelta(days=1, hours=13, minutes=30)).isoformat(),
                "location": "餐厅",
                "participants": ["张三", "客户"],
                "priority": 2
            }
        ]
        
        # 添加示例日程
        for schedule in sample_schedules:
            await ScheduleCSV.create_schedule(DEFAULT_USER_ID, schedule)
        
        print(f"已创建示例日程数据")

# 启动时创建示例数据
@app.on_event("startup")
async def startup_event():
    await create_sample_data()

@app.get("/")
async def root():
    return {"message": "Welcome to AIC Backend API (Simple Version)"}

@app.get("/api/schedule/list")
async def list_schedules():
    # 获取当前日期和30天后的日期作为默认时间范围
    now = datetime.now().isoformat()
    end_date = (datetime.now() + timedelta(days=30)).isoformat()
    
    # 从CSV文件获取日程列表
    schedules = await ScheduleCSV.list_schedules(DEFAULT_USER_ID, now, end_date)
    
    return {
        "status": "success",
        "message": "获取日程列表成功",
        "data": schedules
    }

@app.get("/api/schedule/{schedule_id}")
async def get_schedule(schedule_id: str):
    # 从CSV文件获取特定日程
    schedule = await ScheduleCSV.get_schedule(DEFAULT_USER_ID, schedule_id)
    
    if not schedule:
        return {
            "status": "error",
            "message": "日程不存在",
            "data": None
        }
    
    return {
        "status": "success",
        "message": "获取日程详情成功",
        "data": schedule
    }

@app.post("/api/schedule/create")
async def create_schedule(schedule: Dict[str, Any] = Body(...)):
    # 创建新日程
    try:
        created_schedule = await ScheduleCSV.create_schedule(DEFAULT_USER_ID, schedule)
        return {
            "status": "success",
            "message": "创建日程成功",
            "data": created_schedule
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"创建日程失败: {str(e)}",
            "data": None
        }

@app.put("/api/schedule/{schedule_id}")
async def update_schedule(schedule_id: str, updates: Dict[str, Any] = Body(...)):
    # 更新日程
    updated_schedule = await ScheduleCSV.update_schedule(DEFAULT_USER_ID, schedule_id, updates)
    
    if not updated_schedule:
        return {
            "status": "error",
            "message": "日程不存在或无权更新",
            "data": None
        }
    
    return {
        "status": "success",
        "message": "更新日程成功",
        "data": updated_schedule
    }

@app.delete("/api/schedule/{schedule_id}")
async def delete_schedule(schedule_id: str):
    # 删除日程
    success = await ScheduleCSV.delete_schedule(DEFAULT_USER_ID, schedule_id)
    
    if not success:
        return {
            "status": "error",
            "message": "日程不存在或无权删除",
            "data": None
        }
    
    return {
        "status": "success",
        "message": "删除日程成功",
        "data": {"id": schedule_id}
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
