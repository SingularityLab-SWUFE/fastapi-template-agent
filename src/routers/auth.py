"""认证相关路由

提供登录、刷新、注销等认证接口。
"""

from fastapi import APIRouter, Request, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from src.core.decorators.response import handle_request
from src.auth.dependencies import get_current_user, _get_token_manager
from src.core.schemas.user import User
from src.auth.token_manager import TokenManager


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """刷新 Token 请求模型"""
    refresh_token: str = Field(..., description="刷新 Token")


class RefreshResponse(BaseModel):
    """刷新 Token 响应模型"""
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    """用户信息响应模型"""
    id: int
    username: str
    is_active: bool
    is_superuser: bool


@router.post("/login", response_model=LoginResponse)
@handle_request
async def login(request: Request, login_data: LoginRequest) -> Dict[str, Any]:
    """用户登录

    Args:
        request: FastAPI 请求对象
        login_data: 登录凭据（用户名/邮箱 + 密码）

    Returns:
        包含 access_token 和 refresh_token 的响应

    Raises:
        HTTPException: 登录失败（用户名/密码错误、用户被禁用等）
    """
    token_manager = _get_token_manager()

    # 这里应该使用 UserManager.authenticate 进行认证
    # 为了简化演示，我们先模拟认证逻辑
    # 实际实现时需要连接数据库验证用户

    # TODO: 实现用户认证逻辑
    # - 验证用户名/邮箱和密码
    # - 检查用户是否活跃
    # - 生成 token 对

    # 暂时返回错误，等待实现
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="登录功能尚未实现，请使用数据库验证用户"
    )


@router.post("/refresh", response_model=RefreshResponse)
@handle_request
async def refresh_token(
    request: Request, refresh_data: RefreshRequest
) -> Dict[str, Any]:
    """刷新 access_token

    Args:
        request: FastAPI 请求对象
        refresh_data: 刷新 Token 数据

    Returns:
        新的 access_token

    Raises:
        HTTPException: 刷新 Token 无效或已过期
    """
    token_manager = _get_token_manager()

    # 验证 refresh_token
    user_id = token_manager.verify_refresh_token(refresh_data.refresh_token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新 Token",
        )

    # TODO: 获取用户信息并生成新的 access_token
    # 需要从数据库获取用户信息

    # 暂时返回错误，等待实现
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="刷新 Token 功能尚未实现，需要从数据库获取用户信息"
    )


@router.post("/logout")
@handle_request
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """用户注销

    撤销当前的 access_token（加入黑名单），但不撤销 refresh_token。

    Args:
        request: FastAPI 请求对象
        current_user: 当前认证用户

    Returns:
        注销成功消息

    Raises:
        HTTPException: 注销失败
    """
    # 从请求头获取 token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少认证 Token",
        )

    token = auth_header.split(" ")[1]

    token_manager = _get_token_manager()
    success = token_manager.revoke_access_token(token)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="撤销 Token 失败",
        )

    return {"message": "注销成功"}


@router.get("/me", response_model=UserInfo)
@handle_request
async def get_current_user_info(
    request: Request, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取当前用户信息

    Args:
        request: FastAPI 请求对象
        current_user: 当前认证用户

    Returns:
        当前用户信息
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
    }


@router.get("/sessions")
@handle_request
async def get_user_sessions(
    request: Request, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取用户当前活跃的会话信息

    Args:
        request: FastAPI 请求对象
        current_user: 当前认证用户

    Returns:
        会话信息

    Note:
        这里可以返回用户当前的 refresh_token 信息
    """
    # TODO: 实现获取用户会话信息
    # 需要从 Redis 获取用户的活跃 refresh_token

    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "sessions": [
            {
                "device": "default",
                "last_active": "2025-12-01T10:00:00Z",
                # "refresh_token_id": "..."  # 不应该返回实际的 refresh_token
            }
        ]
    }
