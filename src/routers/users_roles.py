"""用户角色管理路由

提供用户角色的分配、查询、撤销等接口。
"""

from fastapi import APIRouter, Request, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlmodel import select

from src.core.decorators.response import handle_request
from src.auth.dependencies import get_current_superuser
from src.core.schemas.user import User
from src.core.schemas.role import Role
from src.services.permission_service import PermissionService


router = APIRouter(prefix="/api/v1/users", tags=["users-roles"])


class AssignRoleRequest(BaseModel):
    """分配角色请求模型"""
    role_id: int = Field(..., description="角色 ID")


class RoleInfo(BaseModel):
    """角色信息模型"""
    id: int
    name: str
    description: Optional[str]
    is_system: bool


@router.get("/{user_id}/roles", response_model=List[RoleInfo])
@handle_request
async def get_user_roles(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_superuser),
) -> List[Dict[str, Any]]:
    """获取用户的所有角色

    Args:
        request: FastAPI 请求对象
        user_id: 用户 ID
        current_user: 当前超级用户

    Returns:
        用户角色列表

    Raises:
        HTTPException: 用户不存在或权限不足
    """
    from src.session import get_session

    # 检查用户是否存在
    async with get_session() as session:
        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
            )

    # 获取用户角色
    roles = await PermissionService.get_user_roles(user_id)

    return [
        {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_system": role.is_system,
        }
        for role in roles
    ]


@router.post("/{user_id}/roles", response_model=Dict[str, str])
@handle_request
async def assign_role_to_user(
    request: Request,
    user_id: int,
    role_data: AssignRoleRequest,
    current_user: User = Depends(get_current_superuser),
) -> Dict[str, str]:
    """为用户分配角色

    Args:
        request: FastAPI 请求对象
        user_id: 用户 ID
        role_data: 角色数据
        current_user: 当前超级用户

    Returns:
        分配成功消息

    Raises:
        HTTPException: 用户或角色不存在、已分配、权限不足等
    """
    from src.session import get_session

    # 检查用户是否存在
    async with get_session() as session:
        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
            )

        # 检查角色是否存在
        role_result = await session.exec(select(Role).where(Role.id == role_data.role_id))
        role = role_result.first()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在"
            )

    # 分配角色
    success = await PermissionService.assign_role_to_user(user_id, role_data.role_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"用户已是 '{role.name}' 角色的成员",
        )

    return {"message": f"角色 '{role.name}' 已分配给用户"}


@router.delete("/{user_id}/roles/{role_id}", response_model=Dict[str, str])
@handle_request
async def remove_role_from_user(
    request: Request,
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_superuser),
) -> Dict[str, str]:
    """从用户移除角色

    Args:
        request: FastAPI 请求对象
        user_id: 用户 ID
        role_id: 角色 ID
        current_user: 当前超级用户

    Returns:
        移除成功消息

    Raises:
        HTTPException: 用户或角色不存在、未分配、权限不足等
    """
    from src.session import get_session

    # 检查用户是否存在
    async with get_session() as session:
        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
            )

        # 检查角色是否存在
        role_result = await session.exec(select(Role).where(Role.id == role_id))
        role = role_result.first()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在"
            )

    # 移除角色
    success = await PermissionService.remove_role_from_user(user_id, role_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户不是 '{role.name}' 角色的成员",
        )

    return {"message": f"角色 '{role.name}' 已从用户移除"}


# 导入依赖
from src.session import get_session
