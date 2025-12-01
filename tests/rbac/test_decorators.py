"""RBAC 装饰器单元测试"""

import pytest

from src.auth.rbac import (
    require_role,
    require_permission,
    require_any_role,
    require_all_permissions,
    require_superuser,
    require_active_user,
)


class TestRBACDecorators:
    """RBAC 装饰器测试套件"""

    def test_require_role_decorator(self):
        """测试角色检查装饰器"""

        @require_role("admin", "moderator")
        async def admin_endpoint():
            return "admin_access"

        # 装饰器应该被正确应用
        assert callable(admin_endpoint)

    def test_require_permission_decorator(self):
        """测试权限检查装饰器"""

        @require_permission("user.create", "user.edit")
        async def user_management_endpoint():
            return "user_management_access"

        # 装饰器应该被正确应用
        assert callable(user_management_endpoint)

    def test_require_any_role_decorator(self):
        """测试任一角色装饰器"""

        @require_any_role("admin", "moderator")
        async def any_role_endpoint():
            return "any_role_access"

        # 装饰器应该被正确应用
        assert callable(any_role_endpoint)

    def test_require_all_permissions_decorator(self):
        """测试所有权限装饰器"""

        @require_all_permissions("user.create", "user.edit", "user.delete")
        async def all_permissions_endpoint():
            return "all_permissions_access"

        # 装饰器应该被正确应用
        assert callable(all_permissions_endpoint)

    def test_require_superuser_decorator(self):
        """测试超级用户装饰器"""

        @require_superuser
        async def superuser_endpoint():
            return "superuser_access"

        # 装饰器应该被正确应用
        assert callable(superuser_endpoint)

    def test_require_active_user_decorator(self):
        """测试活跃用户装饰器"""

        @require_active_user
        async def active_user_endpoint():
            return "active_user_access"

        # 装饰器应该被正确应用
        assert callable(active_user_endpoint)

    def test_decorator_function_metadata(self):
        """测试装饰器保持函数元数据"""

        @require_role("admin")
        async def sample_endpoint():
            """Sample function docstring."""
            return "test"

        # 装饰器应该保持函数名
        assert sample_endpoint.__name__ == "sample_endpoint"

        # 装饰器应该保持函数文档
        assert sample_endpoint.__doc__ == "Sample function docstring."

    def test_multiple_decorators(self):
        """测试多个装饰器叠加"""

        @require_superuser
        @require_permission("user.delete")
        async def complex_endpoint():
            return "complex_access"

        # 装饰器应该被正确应用
        assert callable(complex_endpoint)
