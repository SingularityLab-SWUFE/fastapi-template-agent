from collections.abc import Sequence
from typing import Literal

import inspect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.schemas.rbac import Permission, Role, RolePermission, UserRole


class PermissionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _split_permission(perm: str) -> tuple[str, str | None]:
        """Split permission into (module, action)."""
        if ":" in perm:
            module, action = perm.split(":", 1)
            return module, action
        return perm, None

    def _match_permission(
        self,
        required_perm: str,
        user_perm: str,
        wildcard_support: bool,
    ) -> bool:
        if not wildcard_support:
            return required_perm == user_perm

        if user_perm == "*":
            return True
        if required_perm == "*":
            return user_perm == "*"

        req_module, req_action = self._split_permission(required_perm)
        user_module, user_action = self._split_permission(user_perm)

        if req_module != user_module:
            return False

        if req_action is None:
            return user_action is None

        if req_action == "*":
            return True

        return user_action == req_action or user_action == "*"

    async def get_user_permissions(self, user_id: int) -> set[str]:
        stmt = (
            select(Permission.code)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(UserRole, RolePermission.role_id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        scalar_result = result.scalars()
        if inspect.iscoroutine(scalar_result):
            scalar_result = await scalar_result
        records = scalar_result.all()
        if inspect.iscoroutine(records):
            records = await records
        return set(records)

    async def get_user_roles(self, user_id: int) -> set[str]:
        stmt = (
            select(Role.name)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        scalar_result = result.scalars()
        if inspect.iscoroutine(scalar_result):
            scalar_result = await scalar_result
        records = scalar_result.all()
        if inspect.iscoroutine(records):
            records = await records
        return set(records)

    async def check_permissions(
        self,
        user_id: int,
        required_perms: Sequence[str],
        match: Literal["all", "any"] = "all",
        wildcard_support: bool = True,
    ) -> bool:
        user_perms = await self.get_user_permissions(user_id)

        if not required_perms:
            return True

        matched = []
        for required_perm in required_perms:
            matched.append(
                any(
                    self._match_permission(required_perm, user_perm, wildcard_support)
                    for user_perm in user_perms
                ),
            )

        return all(matched) if match == "all" else any(matched)

    async def check_roles(
        self,
        user_id: int,
        required_roles: Sequence[str],
        match: Literal["all", "any"] = "all",
    ) -> bool:
        user_roles = await self.get_user_roles(user_id)

        if not required_roles:
            return True

        matched = [required_role in user_roles for required_role in required_roles]

        return all(matched) if match == "all" else any(matched)
