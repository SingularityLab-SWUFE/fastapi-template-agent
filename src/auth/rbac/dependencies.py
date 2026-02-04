from collections.abc import Awaitable, Callable, Sequence
from typing import Literal

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit import AuditService, generate_request_id, get_audit_service
from src.audit.schemas import AuditAction, AuditResult
from src.auth import current_user
from src.auth.exceptions import (
    InsufficientPermissionException,
    InsufficientRoleException,
)
from src.auth.models import User
from src.http.utils import extract_client_info
from src.session import get_session

from .repository import PermissionRepository
from .service import PermissionService


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
