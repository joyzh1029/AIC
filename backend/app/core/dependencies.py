"""
API路由依赖项模块
此模块提供API路由使用的各种依赖项函数
"""
from fastapi import Depends, HTTPException, status, Request, Header
from typing import Optional, List, Dict, Any
import time
from fastapi.security import OAuth2PasswordBearer
import logging

# 设置日志
logger = logging.getLogger(__name__)

# 可选的OAuth2认证（如果项目需要）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# 请求计时中间件
async def measure_execution_time(request: Request, call_next):
    """测量API请求执行时间的中间件"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Request to {request.url.path} took {process_time:.4f} seconds")
    return response

# API版本依赖
async def get_api_version(
    x_api_version: Optional[str] = Header(None, description="API版本")
) -> str:
    """获取API版本的依赖项"""
    if x_api_version is None:
        return "v1"  # 默认版本
    return x_api_version

# 可选的用户认证依赖
async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[Dict[str, Any]]:
    """
    获取当前用户的依赖项
    如果未提供令牌，则返回None（允许匿名访问）
    如果提供了无效令牌，则引发异常
    """
    if token is None:
        return None
    
    # 这里应该实现令牌验证逻辑
    # 示例实现，实际项目中应替换为真实的验证逻辑
    try:
        # 模拟令牌验证
        user = {"id": "user123", "username": "testuser"}
        return user
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

# 必需的用户认证依赖
async def get_current_active_user(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    获取当前活跃用户的依赖项
    要求用户必须已认证
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

# 通用错误处理
def handle_exceptions(request: Request, exc: Exception) -> Dict[str, Any]:
    """统一的异常处理函数"""
    logger.error(f"Error processing request {request.url.path}: {str(exc)}")
    
    if isinstance(exc, HTTPException):
        return {
            "success": False,
            "error": {
                "code": exc.status_code,
                "message": exc.detail
            }
        }
    
    # 处理其他类型的异常
    return {
        "success": False,
        "error": {
            "code": 500,
            "message": "服务器内部错误"
        }
    }
