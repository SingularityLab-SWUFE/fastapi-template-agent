from collections.abc import Awaitable, Callable, Sequence
from typing import Literal

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.schemas import User
from src.core.schemas.rbac import Permission, Role, RolePermission, UserRole
from src.exceptions import InsufficientPermissionException, InsufficientRoleException
from src.session import get_session

from . import current_user


class PermissionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_permissions(self, user_id: int) -> set[str]:
        stmt = (
            select(Permission.code)
            .distinct()
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(UserRole, RolePermission.role_id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return set(result.scalars().all())

    async def get_user_roles(self, user_id: int) -> set[str]:
        stmt = (
            select(Role.name)
            .distinct()
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return set(result.scalars().all())


class PermissionService:
    def __init__(self, repository: PermissionRepository):
        self.repository = repository

    @staticmethod
    def _split_permission(perm: str) -> tuple[str, str | None]:
        """Split permission into (module, action)."""
        if ":" in perm:
            module, action = perm.split(":", 1)
            # Treat empty action as absent (not a wildcard).
            return module, action if action != "" else None
        return perm, None

    def _match_permission(
        self,
        required_perm: str,
        user_perm: str,
        wildcard_support: bool,
    ) -> bool:
        # Wildcard disabled: exact match only
        if not wildcard_support:
            return required_perm == user_perm

        # "*": requires global permission, only user="*" satisfies
        if required_perm == "*":
            return user_perm == "*"
        # user="*": global permission satisfies any requirement
        if user_perm == "*":
            return True

        req_module, req_action = self._split_permission(required_perm)
        user_module, user_action = self._split_permission(user_perm)

        # Different modules: no match
        if req_module != user_module:
            return False

        # required_perm must be "module:action" format (not bare "module")
        if req_action is None:
            return False

        # user has "module" (full module access): matches any "module:action"
        if user_action is None:
            return True

        # "module:*": module wildcard, matches any action
        if req_action == "*":
            return True

        # Exact action match or user has "module:*"
        return user_action == req_action or user_action == "*"

    async def check_permissions(
        self,
        user_id: int,
        required_perms: Sequence[str],
        match: Literal["all", "any"] = "all",
        wildcard_support: bool = True,
    ) -> bool:
        if match not in ("all", "any"):
            raise ValueError("match must be 'all' or 'any'")

        if not required_perms:
            return True

        user_perms = await self.repository.get_user_permissions(user_id)

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
        if match not in ("all", "any"):
            raise ValueError("match must be 'all' or 'any'")

        if not required_roles:
            return True

        user_roles = await self.repository.get_user_roles(user_id)

        matched = [required_role in user_roles for required_role in required_roles]

        return all(matched) if match == "all" else any(matched)


async def get_permission_service(
    session: AsyncSession = Depends(get_session),
) -> PermissionService:
    repository = PermissionRepository(session=session)
    return PermissionService(repository=repository)


def require_permissions(
    *perms: str,
    match: Literal["all", "any"] = "all",
    bypass_superuser: bool = False,
    wildcard_support: bool = True,
):
    async def dependency(
        permission_service: PermissionService = Depends(get_permission_service),
        user: User = Depends(current_user),
    ):
        if bypass_superuser and user.is_superuser:
            return

        has_perms = await permission_service.check_permissions(
            user_id=user.id,
            required_perms=perms,
            match=match,
            wildcard_support=wildcard_support,
        )

        if not has_perms:
            raise InsufficientPermissionException(required=list(perms))

    return dependency


def require_roles(
    *roles: str,
    match: Literal["all", "any"] = "all",
    bypass_superuser: bool = False,
):
    async def dependency(
        permission_service: PermissionService = Depends(get_permission_service),
        user: User = Depends(current_user),
    ):
        if bypass_superuser and user.is_superuser:
            return

        has_roles = await permission_service.check_roles(
            user_id=user.id,
            required_roles=roles,
            match=match,
        )

        if not has_roles:
            raise InsufficientRoleException(required=list(roles))

    return dependency


def owner_or_perm(
    get_owner_id: Callable[..., Awaitable[int]],
    perms: list[str],
    match: Literal["all", "any"] = "all",
    bypass_superuser: bool = False,
    wildcard_support: bool = True,
):
    async def dependency(
        request: Request,
        permission_service: PermissionService = Depends(get_permission_service),
        user: User = Depends(current_user),
    ):
        if bypass_superuser and user.is_superuser:
            return

        kwargs = dict(request.path_params)
        for k, v in kwargs.items():
            try:
                kwargs[k] = int(v)
            except (ValueError, TypeError):
                pass

        owner_id = await get_owner_id(**kwargs)

        if user.id == owner_id:
            return

        has_perms = await permission_service.check_permissions(
            user_id=user.id,
            required_perms=perms,
            match=match,
            wildcard_support=wildcard_support,
        )

        if not has_perms:
            raise InsufficientPermissionException(required=perms)

    return dependency
