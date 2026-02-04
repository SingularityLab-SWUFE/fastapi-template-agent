"""RBAC (Role-Based Access Control) submodule for authorization."""

from .dependencies import (
    get_permission_service,
    owner_or_perm,
    require_permissions,
    require_roles,
)
from .models import Permission, Role, RolePermission, UserRole
from .repository import PermissionRepository
from .service import PermissionService

__all__ = [
    "PermissionRepository",
    "PermissionService",
    "get_permission_service",
    "require_permissions",
    "require_roles",
    "owner_or_perm",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
]
