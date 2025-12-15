from fastapi_users import FastAPIUsers

from src.core.schemas import User

from .backend import auth_backend
from .manager import get_user_manager

fastapi_users = FastAPIUsers[User, int](
    get_user_manager=get_user_manager,
    auth_backends=[auth_backend],
)

current_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)

from .permissions import (  # noqa: E402
    PermissionService,
    get_permission_service,
    owner_or_perm,
    require_active_user,
    require_permissions,
    require_roles,
    require_superuser,
)

__all__ = [
    "PermissionService",
    "auth_backend",
    "current_superuser",
    "current_user",
    "fastapi_users",
    "get_permission_service",
    "get_user_manager",
    "owner_or_perm",
    "require_active_user",
    "require_permissions",
    "require_roles",
    "require_superuser",
]
