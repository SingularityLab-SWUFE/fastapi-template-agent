"""基于角色的访问控制（RBAC）装饰器

提供装饰器用于 API 端点的权限检查。

## 推荐用法

**强烈推荐使用 Depends 方式**，装饰器仅作为语法糖：

```python
# 推荐：使用 Depends
@router.get("/admin")
async def admin_endpoint(
    current_user: User = Depends(require_roles('admin'))
):
    pass

# 可选：使用装饰器（不推荐，需要手动传递 current_user）
@require_role('admin')
async def admin_endpoint(current_user: User = Depends(get_current_user)):
    pass
```

装饰器无法直接访问数据库，因此权限检查逻辑在 dependencies.py 中实现。
"""

from functools import wraps
from typing import Callable, Any, List, Optional

from fastapi import HTTPException, Depends, status


def require_role(*required_roles: str):
    """装饰器：要求用户拥有指定角色

    Args:
        *required_roles: 必需的角色列表（用户需要拥有其中任一角色）

    Note:
        **推荐使用 Depends 方式**：
        `Depends(require_roles(*required_roles))`

    Usage:
        # 推荐用法
        async def endpoint(current_user: User = Depends(require_roles('admin', 'moderator'))):
            pass

        # 装饰器用法（不推荐）
        @require_role('admin', 'moderator')
        async def endpoint(current_user: User = Depends(get_current_user)):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 装饰器仅为语法糖，不执行实际权限检查
            # 实际权限检查通过 dependencies.py 中的 require_roles 实现
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_permission(*required_permissions: str):
    """装饰器：要求用户拥有指定权限

    Args:
        *required_permissions: 必需的权限列表（用户需要拥有所有权限）

    Note:
        **推荐使用 Depends 方式**：
        `Depends(require_permissions(*required_permissions))`

    Usage:
        # 推荐用法
        async def endpoint(current_user: User = Depends(require_permissions('user.create', 'user.edit'))):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 装饰器仅为语法糖，实际权限检查通过 dependencies 实现
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_any_role(*required_roles: str):
    """装饰器：要求用户拥有任一指定角色（与 require_role 相同）

    Args:
        *required_roles: 必需的角色列表

    Note:
        **推荐使用 Depends 方式**：
        `Depends(require_roles(*required_roles))`
    """
    return require_role(*required_roles)


def require_all_permissions(*required_permissions: str):
    """装饰器：要求用户拥有所有指定权限

    Args:
        *required_permissions: 必需的权限列表（用户必须拥有所有权限）

    Note:
        **推荐使用 Depends 方式**：
        `Depends(require_permissions(*required_permissions))`
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 装饰器仅为语法糖，实际权限检查通过 dependencies 实现
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_superuser(func: Callable) -> Callable:
    """装饰器：要求用户为超级用户

    Note:
        **推荐使用 Depends 方式**：
        `Depends(get_current_superuser)`

    Usage:
        # 推荐用法
        async def admin_only_endpoint(
            current_user: User = Depends(get_current_superuser)
        ):
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # 装饰器仅为语法糖，实际权限检查通过 dependencies 实现
        return await func(*args, **kwargs)

    return wrapper


def require_active_user(func: Callable) -> Callable:
    """装饰器：要求用户为活跃用户

    Note:
        **推荐使用 Depends 方式**：
        `Depends(get_current_active_user)`

    Usage:
        # 推荐用法
        async def user_endpoint(
            current_user: User = Depends(get_current_active_user)
        ):
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # 装饰器仅为语法糖，实际权限检查通过 dependencies 实现
        return await func(*args, **kwargs)

    return wrapper
