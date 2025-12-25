from fastapi import Depends, Request
from fastapi_users import FastAPIUsers

from src.audit import AuditService, get_audit_service
from src.audit.dependencies import generate_request_id
from src.audit.schemas import AuditAction, AuditResult
from src.audit.service import extract_client_info
from src.auth.models import User

from .backend import auth_backend
from .manager import get_user_manager

fastapi_users = FastAPIUsers[User, int](
    get_user_manager=get_user_manager,
    auth_backends=[auth_backend],
)

_current_user_base = fastapi_users.current_user(active=True)
_current_superuser_base = fastapi_users.current_user(active=True, superuser=True)


async def current_user(
    request: Request,
    user: User = Depends(_current_user_base),
    audit_service: AuditService = Depends(get_audit_service),
    request_id: str = Depends(generate_request_id),
) -> User:
    user_agent, ip = extract_client_info(request)

    await audit_service.log(
        action=AuditAction.PROTECTED_RESOURCE_ACCESS,
        result=AuditResult.SUCCESS,
        actor_id=user.id,
        request_id=request_id,
        user_agent=user_agent,
        ip=ip,
        extra={
            "method": request.method,
            "path": request.url.path,
        },
    )

    return user


async def current_superuser(
    request: Request,
    user: User = Depends(_current_superuser_base),
    audit_service: AuditService = Depends(get_audit_service),
    request_id: str = Depends(generate_request_id),
) -> User:
    user_agent, ip = extract_client_info(request)

    await audit_service.log(
        action=AuditAction.PROTECTED_RESOURCE_ACCESS,
        result=AuditResult.SUCCESS,
        actor_id=user.id,
        request_id=request_id,
        user_agent=user_agent,
        ip=ip,
        extra={
            "method": request.method,
            "path": request.url.path,
            "superuser": True,
        },
    )

    return user


from .models import (  # noqa: E402
    OAuthAccount,
    Permission,
    Role,
    RolePermission,
    UserRole,
)
from .rbac import (  # noqa: E402
    owner_or_perm,
    require_permissions,
    require_roles,
)
from .schemas import (  # noqa: E402
    AccessTokenResponse,
    MessageResponse,
    TokenResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)

__all__ = [
    "fastapi_users",
    "current_user",
    "current_superuser",
    "require_permissions",
    "require_roles",
    "owner_or_perm",
    "User",
    "OAuthAccount",
    "Permission",
    "Role",
    "RolePermission",
    "UserRole",
    "UserRead",
    "UserCreate",
    "UserUpdate",
    "TokenResponse",
    "AccessTokenResponse",
    "MessageResponse",
]
