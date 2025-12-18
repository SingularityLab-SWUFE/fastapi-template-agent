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

from .rbac import (  # noqa: E402
    require_permissions,
    require_roles,
    owner_or_perm,
)

__all__ = [
    "fastapi_users",
    "current_user",
    "current_superuser",
    "require_permissions",
    "require_roles",
    "owner_or_perm",
]
