from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 创建FastAPI应用
app = FastAPI(title="AIC Backend API", description="AI Companion Backend API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由
from routes import schedule_routes

# 注册路由
app.include_router(schedule_routes.router, prefix="/api/schedule", tags=["Schedule"])

@app.get("/")
async def root():
    return {"message": "Welcome to AIC Backend API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
