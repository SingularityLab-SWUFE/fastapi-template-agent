"""认证依赖注入

提供 FastAPI Depends 依赖，用于获取当前用户、验证 token 等。
"""

from typing import Optional, Generator, List
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import select

from src.core.schemas.user import User, UserRole
from src.core.schemas.role import Role
from src.auth.token_manager import TokenManager
from src.session import get_session


# HTTP Bearer 认证方案
security = HTTPBearer(auto_error=False)


# 全局 Token 管理器实例（在应用启动时初始化）
_token_manager: Optional[TokenManager] = None


def set_token_manager(token_manager: TokenManager) -> None:
    """设置全局 Token 管理器

    Args:
        token_manager: Token 管理器实例
    """
    global _token_manager
    _token_manager = token_manager


def _get_token_manager() -> TokenManager:
    """获取 Token 管理器

    Returns:
        Token 管理器实例

    Raises:
        RuntimeError: 如果 Token 管理器未初始化
    """
    if _token_manager is None:
        raise RuntimeError("Token 管理器未初始化，请先调用 set_token_manager()")
    return _token_manager


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    """获取当前认证用户

    Args:
        credentials: HTTP 认证凭据

    Returns:
        当前用户对象

    Raises:
        HTTPException: 认证失败
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    token_manager = _get_token_manager()

    # 验证 access_token
    payload = await token_manager.verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 获取用户 ID
    user_id = int(payload.get("sub"))
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 中缺少用户 ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 从数据库获取用户
    async with get_session() as session:
        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已被禁用",
            )

        return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户

    Args:
        current_user: 当前用户

    Returns:
        活跃用户对象

    Raises:
        HTTPException: 用户未激活
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前超级用户

    Args:
        current_user: 当前用户

    Returns:
        超级用户对象

    Raises:
        HTTPException: 用户不是超级用户
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="权限不足"
        )
    return current_user


async def get_user_roles(user: User = Depends(get_current_user)) -> List[str]:
    """获取用户的所有角色

    Args:
        user: 当前用户

    Returns:
        角色名称列表
    """
    async with get_session() as session:
        result = await session.exec(
            select(Role.name)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user.id)
        )
        return result.all()


async def get_user_permissions(user: User = Depends(get_current_user)) -> List[str]:
    """获取用户的所有权限代码

    Args:
        user: 当前用户

    Returns:
        权限代码列表
    """
    from src.core.schemas.role import Permission

    async with get_session() as session:
        result = await session.exec(
            select(Permission.code)
            .join(
                RolePermission,
                Permission.id == RolePermission.permission_id,
            )
            .join(
                UserRole,
                Role.id == UserRole.role_id,
            )
            .where(UserRole.user_id == user.id)
        )
        return result.all()


async def require_roles(*required_roles: str):
    """依赖工厂：要求用户拥有指定角色

    Args:
        *required_roles: 必需的角色列表

    Returns:
        依赖函数

    Raises:
        HTTPException: 用户缺少必需角色
    """
    async def _require_roles(
        user: User = Depends(get_current_user),
    ) -> User:
        async with get_session() as session:
            result = await session.exec(
                select(Role.name)
                .join(UserRole, Role.id == UserRole.role_id)
                .where(UserRole.user_id == user.id)
            )
            user_roles = result.all()

            # 检查是否拥有任一必需角色
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要以下角色之一: {', '.join(required_roles)}",
                )

        return user

    return _require_roles


async def require_permissions(*required_permissions: str):
    """依赖工厂：要求用户拥有指定权限

    Args:
        *required_permissions: 必需的权限列表

    Returns:
        依赖函数

    Raises:
        HTTPException: 用户缺少必需权限
    """
    async def _require_permissions(
        user: User = Depends(get_current_user),
    ) -> User:
        from src.core.schemas.role import Permission

        async with get_session() as session:
            result = await session.exec(
                select(Permission.code)
                .join(
                    RolePermission,
                    Permission.id == RolePermission.permission_id,
                )
                .join(
                    UserRole,
                    Role.id == UserRole.role_id,
                )
                .where(UserRole.user_id == user.id)
            )
            user_permissions = result.all()

            # 检查是否拥有所有必需权限
            if not all(
                perm in user_permissions for perm in required_permissions
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要以下权限: {', '.join(required_permissions)}",
                )

        return user

    return _require_permissions
