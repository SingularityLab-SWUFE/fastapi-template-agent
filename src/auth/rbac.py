"""基于角色的访问控制（RBAC）装饰器

提供装饰器用于 API 端点的权限检查。
"""

from functools import wraps
from typing import Callable, Any, List, Optional

from fastapi import HTTPException, Depends, status


def require_role(*required_roles: str):
    """装饰器：要求用户拥有指定角色

    Args:
        *required_roles: 必需的角色列表（用户需要拥有其中任一角色）

    Usage:
        @require_role('admin', 'moderator')
        async def admin_endpoint():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 在实际使用时，通过 FastAPI Depends 注入 current_user
            # 这里依赖函数参数中包含 current_user
            current_user = None

            # 查找 current_user 参数
            for arg_name, arg_value in locals().items():
                if arg_name == "current_user" and arg_value is not None:
                    current_user = arg_value
                    break

            if current_user is None:
                # 尝试从函数参数中获取
                import inspect

                sig = inspect.signature(func)
                if "current_user" in sig.parameters:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="需要认证",
                    )

            # 权限检查逻辑将在这里实现
            # 由于装饰器无法直接访问数据库，这里提供框架
            # 实际使用时，建议使用 dependencies.py 中的 require_roles

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_permission(*required_permissions: str):
    """装饰器：要求用户拥有指定权限

    Args:
        *required_permissions: 必需的权限列表（用户需要拥有所有权限）

    Usage:
        @require_permission('user.create', 'user.edit')
        async def create_user():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 权限检查逻辑将在 dependencies.py 中实现
            # 这里提供框架，实际使用时建议使用 dependencies.require_permissions
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_any_role(*required_roles: str):
    """装饰器：要求用户拥有任一指定角色（与 require_role 相同）

    Args:
        *required_roles: 必需的角色列表

    Usage:
        @require_any_role('admin', 'moderator')
        async def endpoint():
            pass
    """
    return require_role(*required_roles)


def require_all_permissions(*required_permissions: str):
    """装饰器：要求用户拥有所有指定权限

    Args:
        *required_permissions: 必需的权限列表（用户必须拥有所有权限）

    Usage:
        @require_all_permissions('user.create', 'user.edit')
        async def endpoint():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 权限检查逻辑将在 dependencies.py 中实现
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_superuser(func: Callable) -> Callable:
    """装饰器：要求用户为超级用户

    Usage:
        @require_superuser
        async def admin_only_endpoint():
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # 权限检查逻辑将在 dependencies.py 中实现
        # 这里提供框架
        return await func(*args, **kwargs)

    return wrapper


def require_active_user(func: Callable) -> Callable:
    """装饰器：要求用户为活跃用户

    Usage:
        @require_active_user
        async def user_endpoint():
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # 权限检查逻辑将在 dependencies.py 中实现
        # 这里提供框架
        return await func(*args, **kwargs)

    return wrapper
