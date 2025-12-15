from collections.abc import Callable, Sequence
from typing import Any, Awaitable

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.schemas import (
    ErrorCode,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)
from src.exceptions import BusinessException
from src.session import get_session

from . import current_superuser, current_user


class PermissionService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings

    async def _is_superuser(self, user_id: int) -> bool:
        result = await self.session.execute(
            select(User.is_superuser).where(User.id == user_id)
        )
        flag = result.scalar_one_or_none()
        return bool(flag)

    async def get_user_roles(self, user_id: int) -> list[str]:
        if not self.settings.auth.rbac_enabled:
            return []

        result = await self.session.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        roles = set(result.scalars().all())
        if await self._is_superuser(user_id):
            roles.add("superuser")
        return list(roles)

    async def get_user_permissions(self, user_id: int) -> list[str]:
        if not self.settings.auth.rbac_enabled:
            return ["*"] if await self._is_superuser(user_id) else []

        result = await self.session.execute(
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        perms = set(result.scalars().all())
        if await self._is_superuser(user_id):
            perms.add("*")
        return list(perms)

    async def check_permissions(
        self,
        user_id: int,
        required_perms: Sequence[str],
    ) -> bool:
        if not self.settings.auth.rbac_enabled:
            return True

        if not required_perms:
            return True

        perms = await self.get_user_permissions(user_id)
        perm_set = set(perms)
        if "*" in perm_set:
            return True
        return set(required_perms).issubset(perm_set)

    async def check_roles(
        self,
        user_id: int,
        required_roles: Sequence[str],
    ) -> bool:
        if not self.settings.auth.rbac_enabled:
            return True

        if not required_roles:
            return True

        roles = set(await self.get_user_roles(user_id))
        return set(required_roles).issubset(roles)


def get_permission_service(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> PermissionService:
    return PermissionService(session, settings)


def _raise_permission_error() -> None:
    raise BusinessException(ErrorCode.PERM_INSUFFICIENT, "Insufficient permissions")


def require_permissions(*perms: str) -> Callable[..., Awaitable[Any]]:
    async def dependency(
        user=Depends(current_user),
        service: PermissionService = Depends(get_permission_service),
    ):
        allowed = await service.check_permissions(user.id, perms)
        if not allowed:
            _raise_permission_error()
        return user

    return dependency


def require_roles(*roles: str) -> Callable[..., Awaitable[Any]]:
    async def dependency(
        user=Depends(current_user),
        service: PermissionService = Depends(get_permission_service),
    ):
        allowed = await service.check_roles(user.id, roles)
        if not allowed:
            _raise_permission_error()
        return user

    return dependency


def owner_or_perm(
    resource_getter: Callable[..., Any],
    perm: str,
    owner_field: str = "owner_id",
) -> Callable[..., Awaitable[Any]]:
    async def dependency(
        obj=Depends(resource_getter),
        user=Depends(current_user),
        service: PermissionService = Depends(get_permission_service),
    ):
        owner_id = getattr(obj, owner_field, None)
        if owner_id == user.id:
            return obj

        allowed = await service.check_permissions(user.id, [perm])
        if not allowed:
            _raise_permission_error()
        return obj

    return dependency


require_active_user = current_user
require_superuser = current_superuser
