from fastapi_users import FastAPIUsers

from src.core.schemas import User

from .backend import auth_backend
from .manager import get_user_manager
from .rbac import (
    get_rbac_deps,
    require_permissions,
    require_roles,
    owner_or_perm,
    RBACDependencies,
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager=get_user_manager,
    auth_backends=[auth_backend],
)

current_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)

__all__ = [
    "fastapi_users",
    "current_user",
    "current_superuser",
    "get_rbac_deps",
    "require_permissions",
    "require_roles",
    "owner_or_perm",
    "RBACDependencies",
]
