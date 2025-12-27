from collections.abc import Awaitable, Callable, Sequence
from typing import Literal

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit import AuditService, generate_request_id, get_audit_service
from src.audit.schemas import AuditAction, AuditResult
from src.audit.service import extract_client_info
from src.auth.models import Permission, Role, RolePermission, User, UserRole
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

    def _has_permission(
        self,
        required_perm: str,
        user_perms: set[str],
        wildcard_support: bool,
    ) -> bool:
        return any(
            self._match_permission(required_perm, user_perm, wildcard_support)
            for user_perm in user_perms
        )

    async def check_permissions(
        self,
        user_id: int,
        required_perms: Sequence[str],
        match: Literal["all", "any"] = "all",
        wildcard_support: bool = True,
    ) -> bool:
        if match not in ("all", "any"):
            raise ValueError("match must be 'all' or 'any'")

        user_perms = await self.repository.get_user_permissions(user_id)

        if match == "all":
            return all(
                self._has_permission(req, user_perms, wildcard_support)
                for req in required_perms
            )
        return any(
            self._has_permission(req, user_perms, wildcard_support)
            for req in required_perms
        )

    async def check_roles(
        self,
        user_id: int,
        required_roles: Sequence[str],
        match: Literal["all", "any"] = "all",
    ) -> bool:
        if match not in ("all", "any"):
            raise ValueError("match must be 'all' or 'any'")

        user_roles = await self.repository.get_user_roles(user_id)

        if match == "all":
            return all(req in user_roles for req in required_roles)
        return any(req in user_roles for req in required_roles)


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
    if not perms:
        raise ValueError("perms must not be empty")

    async def dependency(
        request: Request,
        permission_service: PermissionService = Depends(get_permission_service),
        user: User = Depends(current_user),
        audit_service: AuditService = Depends(get_audit_service),
        request_id: str = Depends(generate_request_id),
    ):
        user_agent, ip = extract_client_info(request)

        if bypass_superuser and user.is_superuser:
            await audit_service.log(
                action=AuditAction.PERMISSION_CHECK,
                result=AuditResult.GRANTED,
                request_id=request_id,
                actor_id=user.id,
                user_agent=user_agent,
                ip=ip,
                extra={"permissions": list(perms), "bypass": "superuser"},
            )
            return

        has_perms = await permission_service.check_permissions(
            user_id=user.id,
            required_perms=perms,
            match=match,
            wildcard_support=wildcard_support,
        )

        if not has_perms:
            await audit_service.log(
                action=AuditAction.PERMISSION_CHECK,
                result=AuditResult.DENIED,
                request_id=request_id,
                actor_id=user.id,
                user_agent=user_agent,
                ip=ip,
                extra={"permissions": list(perms)},
            )
            raise InsufficientPermissionException(required=list(perms))

        await audit_service.log(
            action=AuditAction.PERMISSION_CHECK,
            result=AuditResult.GRANTED,
            request_id=request_id,
            actor_id=user.id,
            user_agent=user_agent,
            ip=ip,
            extra={"permissions": list(perms)},
        )

    return dependency


def require_roles(
    *roles: str,
    match: Literal["all", "any"] = "all",
    bypass_superuser: bool = False,
):
    if not roles:
        raise ValueError("roles must not be empty")

    async def dependency(
        request: Request,
        permission_service: PermissionService = Depends(get_permission_service),
        user: User = Depends(current_user),
        audit_service: AuditService = Depends(get_audit_service),
        request_id: str = Depends(generate_request_id),
    ):
        user_agent, ip = extract_client_info(request)

        if bypass_superuser and user.is_superuser:
            await audit_service.log(
                action=AuditAction.ROLE_CHECK,
                result=AuditResult.GRANTED,
                request_id=request_id,
                actor_id=user.id,
                user_agent=user_agent,
                ip=ip,
                extra={"roles": list(roles), "bypass": "superuser"},
            )
            return

        has_roles = await permission_service.check_roles(
            user_id=user.id,
            required_roles=roles,
            match=match,
        )

        if not has_roles:
            await audit_service.log(
                action=AuditAction.ROLE_CHECK,
                result=AuditResult.DENIED,
                request_id=request_id,
                actor_id=user.id,
                user_agent=user_agent,
                ip=ip,
                extra={"roles": list(roles)},
            )
            raise InsufficientRoleException(required=list(roles))

        await audit_service.log(
            action=AuditAction.ROLE_CHECK,
            result=AuditResult.GRANTED,
            request_id=request_id,
            actor_id=user.id,
            user_agent=user_agent,
            ip=ip,
            extra={"roles": list(roles)},
        )

    return dependency


def owner_or_perm(
    get_owner_id: Callable[..., Awaitable[int]],
    perms: Sequence[str],
    match: Literal["all", "any"] = "all",
    bypass_superuser: bool = False,
    wildcard_support: bool = True,
):
    async def dependency(
        request: Request,
        permission_service: PermissionService = Depends(get_permission_service),
        user: User = Depends(current_user),
        audit_service: AuditService = Depends(get_audit_service),
        request_id: str = Depends(generate_request_id),
    ):
        user_agent, ip = extract_client_info(request)

        if bypass_superuser and user.is_superuser:
            await audit_service.log(
                action=AuditAction.PERMISSION_CHECK,
                result=AuditResult.GRANTED,
                request_id=request_id,
                actor_id=user.id,
                user_agent=user_agent,
                ip=ip,
                extra={"permissions": list(perms), "bypass": "superuser"},
            )
            return

        kwargs = dict(request.path_params)
        for k, v in kwargs.items():
            try:
                kwargs[k] = int(v)
            except (ValueError, TypeError):
                pass

        owner_id = await get_owner_id(**kwargs)

        if user.id == owner_id:
            await audit_service.log(
                action=AuditAction.PERMISSION_CHECK,
                result=AuditResult.GRANTED,
                request_id=request_id,
                actor_id=user.id,
                user_agent=user_agent,
                ip=ip,
                extra={"permissions": list(perms), "owner": True},
            )
            return

        has_perms = await permission_service.check_permissions(
            user_id=user.id,
            required_perms=perms,
            match=match,
            wildcard_support=wildcard_support,
        )

        if not has_perms:
            await audit_service.log(
                action=AuditAction.PERMISSION_CHECK,
                result=AuditResult.DENIED,
                request_id=request_id,
                actor_id=user.id,
                user_agent=user_agent,
                ip=ip,
                extra={"permissions": list(perms)},
            )
            raise InsufficientPermissionException(required=perms)

        await audit_service.log(
            action=AuditAction.PERMISSION_CHECK,
            result=AuditResult.GRANTED,
            request_id=request_id,
            actor_id=user.id,
            user_agent=user_agent,
            ip=ip,
            extra={"permissions": list(perms)},
        )

    return dependency
