from .dependencies import current_superuser, current_user, fastapi_users
from .models import OAuthAccount, User
from .rbac import (
    Permission,
    Role,
    RolePermission,
    UserRole,
    owner_or_perm,
    require_permissions,
    require_roles,
)
from .schemas import (
    MessageResponse,
    TokenResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)
from .service import AuthenticationService, get_auth_service

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
    "MessageResponse",
    "AuthenticationService",
    "get_auth_service",
]
