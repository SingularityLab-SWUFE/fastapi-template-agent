from collections.abc import Callable, Sequence
from typing import Literal

from fastapi import Depends
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
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(UserRole, RolePermission.role_id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return set(result.scalars().all())

    async def get_user_roles(self, user_id: int) -> set[str]:
        stmt = (
            select(Role.name)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return set(result.scalars().all())


class PermissionService:
    def __init__(
        self,
        session: AsyncSession,
        repository: PermissionRepository | None = None,
    ):
        self.repository = repository or PermissionRepository(session)

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

        # Empty string: public access, no permission required
        if required_perm == "":
            return True

        # "module:" with trailing colon: invalid syntax
        if required_perm.endswith(":") and len(required_perm) > 1:
            return False

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

        # "module" (no action): alias for "module:*", matches any action in module
        if req_action is None:
            return True

        # "module:*": module wildcard, matches any action
        if req_action == "*":
            return True

        # User has "module" but requirement is "module:action": no match
        if user_action is None:
            return False

        # Exact action match or user has "module:*"
        return user_action == req_action or user_action == "*"

    async def get_user_permissions(self, user_id: int) -> set[str]:
        return await self.repository.get_user_permissions(user_id)

    async def get_user_roles(self, user_id: int) -> set[str]:
        return await self.repository.get_user_roles(user_id)

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


async def get_permission_service(
    session: AsyncSession = Depends(get_session),
) -> PermissionService:
    repository = PermissionRepository(session=session)
    return PermissionService(session=session, repository=repository)


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
            user_perms = await permission_service.get_user_permissions(user.id)
            raise InsufficientPermissionException(
                user_id=user.id,
                required=list(perms),
                user_perms=user_perms,
            )

    return Depends(dependency)


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
            user_roles = await permission_service.get_user_roles(user.id)
            raise InsufficientRoleException(
                user_id=user.id,
                required=list(roles),
                user_roles=user_roles,
            )

    return Depends(dependency)


def owner_or_perm(
    get_owner_id: Callable[..., int],
    perms: str | list[str],
    match: Literal["all", "any"] = "all",
    bypass_superuser: bool = False,
    wildcard_support: bool = True,
):
    async def dependency(
        owner_id: int = Depends(get_owner_id),
        permission_service: PermissionService = Depends(get_permission_service),
        user: User = Depends(current_user),
    ):
        if bypass_superuser and user.is_superuser:
            return

        if user.id == owner_id:
            return

        perms_list = [perms] if isinstance(perms, str) else list(perms)

        has_perms = await permission_service.check_permissions(
            user_id=user.id,
            required_perms=perms_list,
            match=match,
            wildcard_support=wildcard_support,
        )

        if not has_perms:
            user_perms = await permission_service.get_user_permissions(user.id)
            raise InsufficientPermissionException(
                user_id=user.id,
                required=perms_list,
                user_perms=user_perms,
            )

    return Depends(dependency)
