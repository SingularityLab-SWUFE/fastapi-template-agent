"""角色管理路由

提供角色的创建、查询、更新、删除等接口。
"""

from fastapi import APIRouter, Request, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlmodel import select

from src.core.decorators.response import handle_request
from src.auth.dependencies import get_current_superuser
from src.core.schemas.user import User
from src.core.schemas.role import Role, Permission
from src.services.permission_service import PermissionService


router = APIRouter(prefix="/api/v1/roles", tags=["roles"])


class RoleCreate(BaseModel):
    """创建角色请求模型"""
    name: str = Field(..., description="角色名称", max_length=100)
    description: Optional[str] = Field(
        None, description="角色描述", max_length=255
    )


class RoleUpdate(BaseModel):
    """更新角色请求模型"""
    name: Optional[str] = Field(
        None, description="角色名称", max_length=100
    )
    description: Optional[str] = Field(
        None, description="角色描述", max_length=255
    )


class RoleResponse(BaseModel):
    """角色响应模型"""
    id: int
    name: str
    description: Optional[str]
    is_system: bool
    created_at: Optional[str]
    updated_at: Optional[str]


@router.get("", response_model=List[RoleResponse])
@handle_request
async def list_roles(
    request: Request,
    current_user: User = Depends(get_current_superuser),
) -> List[Dict[str, Any]]:
    """获取所有角色

    Args:
        request: FastAPI 请求对象
        current_user: 当前超级用户

    Returns:
        角色列表

    Raises:
        HTTPException: 权限不足
    """
    roles = await PermissionService.get_all_roles()

    return [
        {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_system": role.is_system,
            "created_at": role.created_at.isoformat() if role.created_at else None,
            "updated_at": role.updated_at.isoformat() if role.updated_at else None,
        }
        for role in roles
    ]


@router.get("/{role_id}", response_model=RoleResponse)
@handle_request
async def get_role(
    request: Request,
    role_id: int,
    current_user: User = Depends(get_current_superuser),
) -> Dict[str, Any]:
    """获取指定角色信息

    Args:
        request: FastAPI 请求对象
        role_id: 角色 ID
        current_user: 当前超级用户

    Returns:
        角色信息

    Raises:
        HTTPException: 角色不存在或权限不足
    """
    async with get_session() as session:
        result = await session.exec(select(Role).where(Role.id == role_id))
        role = result.first()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在"
            )

        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_system": role.is_system,
            "created_at": role.created_at.isoformat() if role.created_at else None,
            "updated_at": role.updated_at.isoformat() if role.updated_at else None,
        }


@router.post("", response_model=RoleResponse)
@handle_request
async def create_role(
    request: Request,
    role_data: RoleCreate,
    current_user: User = Depends(get_current_superuser),
) -> Dict[str, Any]:
    """创建新角色

    Args:
        request: FastAPI 请求对象
        role_data: 角色数据
        current_user: 当前超级用户

    Returns:
        创建的角色信息

    Raises:
        HTTPException: 角色已存在、权限不足等
    """
    # 检查角色是否已存在
    existing_role = await PermissionService.get_role_by_name(role_data.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="角色已存在"
        )

    # 创建角色
    role = await PermissionService.create_role(
        name=role_data.name, description=role_data.description
    )

    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_system": role.is_system,
        "created_at": role.created_at.isoformat() if role.created_at else None,
        "updated_at": role.updated_at.isoformat() if role.updated_at else None,
    }


@router.put("/{role_id}", response_model=RoleResponse)
@handle_request
async def update_role(
    request: Request,
    role_id: int,
    role_data: RoleUpdate,
    current_user: User = Depends(get_current_superuser),
) -> Dict[str, Any]:
    """更新角色信息

    Args:
        request: FastAPI 请求对象
        role_id: 角色 ID
        role_data: 更新数据
        current_user: 当前超级用户

    Returns:
        更新后的角色信息

    Raises:
        HTTPException: 角色不存在、系统角色不可修改、权限不足等
    """
    from src.session import get_session

    async with get_session() as session:
        result = await session.exec(select(Role).where(Role.id == role_id))
        role = result.first()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在"
            )

        if role.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统角色不可修改",
            )

        # 更新字段
        if role_data.name is not None:
            role.name = role_data.name
        if role_data.description is not None:
            role.description = role_data.description

        await session.commit()
        await session.refresh(role)

        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_system": role.is_system,
            "created_at": role.created_at.isoformat() if role.created_at else None,
            "updated_at": role.updated_at.isoformat() if role.updated_at else None,
        }


@router.delete("/{role_id}")
@handle_request
async def delete_role(
    request: Request,
    role_id: int,
    current_user: User = Depends(get_current_superuser),
) -> Dict[str, str]:
    """删除角色

    Args:
        request: FastAPI 请求对象
        role_id: 角色 ID
        current_user: 当前超级用户

    Returns:
        删除成功消息

    Raises:
        HTTPException: 角色不存在、系统角色不可删除、权限不足等
    """
    from src.session import get_session

    async with get_session() as session:
        result = await session.exec(select(Role).where(Role.id == role_id))
        role = result.first()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在"
            )

        if role.is_system:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="系统角色不可删除",
            )

        await session.delete(role)
        await session.commit()

        return {"message": f"角色 '{role.name}' 已删除"}


@router.get("/{role_id}/permissions", response_model=List[Dict[str, Any]])
@handle_request
async def get_role_permissions(
    request: Request,
    role_id: int,
    current_user: User = Depends(get_current_superuser),
) -> List[Dict[str, Any]]:
    """获取角色的所有权限

    Args:
        request: FastAPI 请求对象
        role_id: 角色 ID
        current_user: 当前超级用户

    Returns:
        权限列表

    Raises:
        HTTPException: 角色不存在或权限不足
    """
    permissions = await PermissionService.get_role_permissions(role_id)

    return [
        {
            "id": perm.id,
            "name": perm.name,
            "code": perm.code,
            "description": perm.description,
            "resource": perm.resource,
            "action": perm.action,
        }
        for perm in permissions
    ]


@router.post("/{role_id}/permissions/{permission_id}")
@handle_request
async def assign_permission_to_role(
    request: Request,
    role_id: int,
    permission_id: int,
    current_user: User = Depends(get_current_superuser),
) -> Dict[str, str]:
    """为角色分配权限

    Args:
        request: FastAPI 请求对象
        role_id: 角色 ID
        permission_id: 权限 ID
        current_user: 当前超级用户

    Returns:
        分配成功消息

    Raises:
        HTTPException: 角色或权限不存在、已分配、权限不足等
    """
    success = await PermissionService.assign_permission_to_role(
        role_id, permission_id
    )

    if not success:
        # 检查是否存在
        from src.session import get_session

        async with get_session() as session:
            role_result = await session.exec(select(Role).where(Role.id == role_id))
            permission_result = await session.exec(
                select(Permission).where(Permission.id == permission_id)
            )

            if not role_result.first():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在"
                )
            if not permission_result.first():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="权限不存在"
                )
            # 如果都存在但分配失败，说明已存在
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="权限已分配给该角色",
            )

    return {"message": "权限分配成功"}


@router.delete("/{role_id}/permissions/{permission_id}")
@handle_request
async def remove_permission_from_role(
    request: Request,
    role_id: int,
    permission_id: int,
    current_user: User = Depends(get_current_superuser),
) -> Dict[str, str]:
    """从角色移除权限

    Args:
        request: FastAPI 请求对象
        role_id: 角色 ID
        permission_id: 权限 ID
        current_user: 当前超级用户

    Returns:
        移除成功消息

    Raises:
        HTTPException: 角色或权限不存在、未分配、权限不足等
    """
    success = await PermissionService.remove_permission_from_role(
        role_id, permission_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限未分配给该角色",
        )

    return {"message": "权限移除成功"}


# 导入依赖
from src.session import get_session
