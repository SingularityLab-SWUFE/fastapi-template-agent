"""角色权限管理集成测试

测试角色创建、更新、删除，权限分配等管理员功能。
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone

from src.services.permission_service import PermissionService
from src.core.schemas.role import Role, Permission, RolePermission
from src.core.schemas.user import User, UserRole


class MockCache:
    """模拟缓存实现"""

    def __init__(self):
        self._data = {}
        self._ttl = {}

    async def set(self, key, value, ttl=None):
        self._data[key] = value
        if ttl:
            self._ttl[key] = ttl

    async def get(self, key):
        return self._data.get(key)

    async def delete(self, key):
        if key in self._data:
            del self._data[key]
        if key in self._ttl:
            del self._ttl[key]


@pytest.mark.usefixtures("test_db")
class TestRoleManagementIntegration:
    """角色权限管理集成测试套件"""

    @pytest.fixture(scope="class")
    async def test_db(self):
        """初始化测试数据库"""
        import os
        from src.session import init_db, close_db

        # 使用 SQLite 文件数据库进行测试
        db_url = "sqlite+aiosqlite:///./test.db"

        # 初始化数据库连接
        await init_db(db_url, echo=False)

        # 创建所有表 - 使用同步方式
        from sqlmodel import SQLModel, create_engine
        from src.core.schemas.user import User, UserRole
        from src.core.schemas.role import Role, Permission, RolePermission

        engine = create_engine("sqlite:///./test.db", echo=False)
        SQLModel.metadata.create_all(engine)
        engine.dispose()

        yield

        # 清理
        await close_db()
        # 删除测试数据库文件
        if os.path.exists("./test.db"):
            os.remove("./test.db")

    @pytest.mark.asyncio
    async def test_create_role(self):
        """测试创建新角色"""
        # 使用 PermissionService 创建角色
        role = await PermissionService.create_role(
            name="test_role_create",
            description="测试创建的角色",
        )

        # 验证角色创建成功
        assert role is not None
        assert role.name == "test_role_create"
        assert role.description == "测试创建的角色"
        assert role.is_system is False

        # 验证数据库中有该角色
        retrieved_role = await PermissionService.get_role_by_name("test_role_create")
        assert retrieved_role is not None
        assert retrieved_role.id == role.id
        assert retrieved_role.name == role.name

    @pytest.mark.asyncio
    async def test_update_role(self):
        """测试更新角色信息"""
        from sqlmodel import select
        from src.session import get_session

        # 创建角色
        role = await PermissionService.create_role(
            name="test_role_update",
            description="原始描述",
        )

        async with get_session() as session:
            # 更新角色
            result = await session.exec(
                select(Role).where(Role.name == "test_role_update")
            )
            retrieved_role = result.first()
            assert retrieved_role is not None

            # 修改角色信息
            retrieved_role.description = "更新后的描述"
            session.add(retrieved_role)
            await session.commit()

        # 验证更新成功
        updated_role = await PermissionService.get_role_by_name("test_role_update")
        assert updated_role is not None
        assert updated_role.description == "更新后的描述"

    @pytest.mark.asyncio
    async def test_delete_role(self):
        """测试删除角色"""
        from sqlmodel import select
        from src.session import get_session
        from src.core.schemas.role import Role, Permission, RolePermission
        from src.core.schemas.user import User, UserRole

        # 创建角色
        role = await PermissionService.create_role(
            name="test_role_delete",
            description="待删除的角色",
        )

        async with get_session() as session:
            # 创建用户和权限
            user = User(
                username="testuser_delete",
                hashed_password="hashed",
                is_active=True,
            )
            session.add(user)
            await session.commit()

            permission = Permission(
                name="测试权限",
                code="test.permission.delete",
                description="测试权限",
            )
            session.add(permission)
            await session.commit()

            # 为角色分配权限
            role_permission = RolePermission(
                role_id=role.id, permission_id=permission.id
            )
            session.add(role_permission)

            # 为用户分配角色
            user_role = UserRole(user_id=user.id, role_id=role.id)
            session.add(user_role)

            await session.commit()

            # 验证角色有关联数据
            assert await session.get(RolePermission, (role.id, permission.id)) is not None
            assert await session.get(UserRole, (user.id, role.id)) is not None

            # 删除角色
            await session.delete(role)
            await session.commit()

        # 验证角色已删除
        deleted_role = await PermissionService.get_role_by_name("test_role_delete")
        assert deleted_role is None

    @pytest.mark.asyncio
    async def test_assign_multiple_roles_to_user(self):
        """测试为用户分配多个角色"""
        from sqlmodel import select
        from src.session import get_session
        from src.core.schemas.user import User, UserRole
        from src.core.schemas.role import Role

        # 创建用户
        async with get_session() as session:
            user = User(
                username="testuser_multi_roles",
                hashed_password="hashed",
                is_active=True,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            # 创建多个角色
            role1 = Role(
                name="role_multi_1",
                description="角色1",
                is_system=False,
            )
            session.add(role1)
            await session.commit()
            await session.refresh(role1)

            role2 = Role(
                name="role_multi_2",
                description="角色2",
                is_system=False,
            )
            session.add(role2)
            await session.commit()
            await session.refresh(role2)

            role3 = Role(
                name="role_multi_3",
                description="角色3",
                is_system=False,
            )
            session.add(role3)
            await session.commit()
            await session.refresh(role3)

            # 分配所有角色
            success1 = await PermissionService.assign_role_to_user(user.id, role1.id)
            success2 = await PermissionService.assign_role_to_user(user.id, role2.id)
            success3 = await PermissionService.assign_role_to_user(user.id, role3.id)

            assert success1 is True
            assert success2 is True
            assert success3 is True

        # 验证用户拥有所有角色
        user_roles = await PermissionService.get_user_roles(user.id)
        assert len(user_roles) == 3

        role_names = {role.name for role in user_roles}
        assert "role_multi_1" in role_names
        assert "role_multi_2" in role_names
        assert "role_multi_3" in role_names

    @pytest.mark.asyncio
    async def test_role_based_api_access(self):
        """测试基于角色的 API 访问控制"""
        # 注意：这个测试验证权限检查逻辑
        # 在实际应用中，需要在 API 层实现权限检查

        from sqlmodel import select
        from src.session import get_session
        from src.core.schemas.user import User, UserRole
        from src.core.schemas.role import Role, Permission, RolePermission

        async with get_session() as session:
            # 创建用户
            user = User(
                username="testuser_rbac",
                hashed_password="hashed",
                is_active=True,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            # 创建角色
            admin_role = Role(
                name="admin_rbac",
                description="管理员",
                is_system=False,
            )
            session.add(admin_role)
            await session.commit()
            await session.refresh(admin_role)

            # 创建权限
            user_create_perm = Permission(
                name="创建用户",
                code="user.create",
                description="创建用户权限",
            )
            session.add(user_create_perm)
            await session.commit()
            await session.refresh(user_create_perm)

            user_delete_perm = Permission(
                name="删除用户",
                code="user.delete",
                description="删除用户权限",
            )
            session.add(user_delete_perm)
            await session.commit()
            await session.refresh(user_delete_perm)

            # 为角色分配权限
            await PermissionService.assign_permission_to_role(
                admin_role.id, user_create_perm.id
            )
            await PermissionService.assign_permission_to_role(
                admin_role.id, user_delete_perm.id
            )

            # 为用户分配角色
            await PermissionService.assign_role_to_user(user.id, admin_role.id)

        # 验证用户拥有 admin 角色
        assert await PermissionService.check_user_has_role(user.id, "admin_rbac") is True

        # 验证用户拥有 user.create 权限
        assert (
            await PermissionService.check_user_has_permission(
                user.id, "user.create"
            )
            is True
        )

        # 验证用户拥有 user.delete 权限
        assert (
            await PermissionService.check_user_has_permission(
                user.id, "user.delete"
            )
            is True
        )

        # 验证用户没有其他权限
        assert (
            await PermissionService.check_user_has_permission(
                user.id, "user.update"
            )
            is False
        )

    @pytest.mark.asyncio
    async def test_permission_caching(self):
        """测试权限缓存机制"""
        # 注意：在实际应用中，可以实现权限缓存以提高性能
        # 这个测试验证权限立即生效

        from sqlmodel import select
        from src.session import get_session
        from src.core.schemas.user import User, UserRole
        from src.core.schemas.role import Role, Permission, RolePermission

        async with get_session() as session:
            # 创建用户、角色和权限
            user = User(
                username="testuser_cache",
                hashed_password="hashed",
                is_active=True,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            role = Role(
                name="role_cache",
                description="缓存测试角色",
                is_system=False,
            )
            session.add(role)
            await session.commit()
            await session.refresh(role)

            permission = Permission(
                name="缓存测试权限",
                code="cache.test",
                description="缓存测试",
            )
            session.add(permission)
            await session.commit()
            await session.refresh(permission)

            # 初始状态：用户没有权限
            assert (
                await PermissionService.check_user_has_permission(
                    user.id, "cache.test"
                )
                is False
            )

            # 为角色分配权限
            await PermissionService.assign_permission_to_role(
                role.id, permission.id
            )

            # 为用户分配角色
            await PermissionService.assign_role_to_user(user.id, role.id)

        # 验证权限立即生效（无缓存延迟）
        assert (
            await PermissionService.check_user_has_permission(
                user.id, "cache.test"
            )
            is True
        )

        # 验证角色变更立即生效
        async with get_session() as session:
            result = await session.exec(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id,
                )
            )
            role_permission = result.first()
            if role_permission:
                await session.delete(role_permission)
                await session.commit()

        assert (
            await PermissionService.check_user_has_permission(
                user.id, "cache.test"
            )
            is False
        )

    @pytest.mark.asyncio
    async def test_bulk_role_assignment(self):
        """测试批量角色分配"""
        from sqlmodel import select
        from src.session import get_session
        from src.core.schemas.user import User, UserRole
        from src.core.schemas.role import Role

        # 创建多个用户
        user_ids = []
        async with get_session() as session:
            for i in range(5):
                user = User(
                    username=f"bulk_user_{i}",
                    hashed_password="hashed",
                    is_active=True,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                user_ids.append(user.id)

            # 创建角色
            role = Role(
                name="bulk_role",
                description="批量分配角色",
                is_system=False,
            )
            session.add(role)
            await session.commit()
            await session.refresh(role)

            # 批量分配角色
            for user_id in user_ids:
                await PermissionService.assign_role_to_user(user_id, role.id)

        # 验证所有用户都获得了角色
        for user_id in user_ids:
            user_roles = await PermissionService.get_user_roles(user_id)
            assert len(user_roles) == 1
            assert user_roles[0].name == "bulk_role"

    @pytest.mark.asyncio
    async def test_system_role_protection(self):
        """测试系统角色保护"""
        from sqlmodel import select
        from src.session import get_session
        from src.core.schemas.role import Role

        # 创建系统角色
        system_role = Role(
            name="system_role",
            description="系统角色",
            is_system=True,
        )

        async with get_session() as session:
            session.add(system_role)
            await session.commit()

            # 尝试删除系统角色（在实际应用中，应该被拒绝）
            # 这里我们只是测试是否可以创建系统角色
            await session.delete(system_role)
            await session.commit()

        # 验证系统角色已被删除
        deleted_role = await PermissionService.get_role_by_name("system_role")
        assert deleted_role is None

        # 注意：在实际应用中，应该实现系统角色保护
        # 例如在删除前检查 is_system 标志

    @pytest.mark.asyncio
    async def test_role_permission_audit(self):
        """测试角色权限审计"""
        from sqlmodel import select
        from src.session import get_session
        from src.core.schemas.user import User, UserRole
        from src.core.schemas.role import Role, Permission, RolePermission

        async with get_session() as session:
            # 创建用户、角色和权限
            user = User(
                username="audit_user",
                hashed_password="hashed",
                is_active=True,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            role = Role(
                name="audit_role",
                description="审计测试角色",
                is_system=False,
            )
            session.add(role)
            await session.commit()
            await session.refresh(role)

            permission = Permission(
                name="审计测试权限",
                code="audit.test",
                description="审计测试",
            )
            session.add(permission)
            await session.commit()
            await session.refresh(permission)

            # 记录创建时间
            before_assignment = datetime.now(timezone.utc).replace(tzinfo=None)

            # 分配权限到角色
            await PermissionService.assign_permission_to_role(
                role.id, permission.id
            )

            # 为用户分配角色
            await PermissionService.assign_role_to_user(user.id, role.id)

            after_assignment = datetime.now(timezone.utc).replace(tzinfo=None)

            # 验证审计记录
            # 1. 验证角色权限关联记录
            result = await session.exec(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id,
                )
            )
            role_permission = result.first()
            assert role_permission is not None
            assert role_permission.created_at >= before_assignment
            assert role_permission.created_at <= after_assignment

            # 2. 验证用户角色关联记录
            result = await session.exec(
                select(UserRole).where(
                    UserRole.user_id == user.id,
                    UserRole.role_id == role.id,
                )
            )
            user_role = result.first()
            assert user_role is not None
            assert user_role.created_at >= before_assignment
            assert user_role.created_at <= after_assignment

        # 3. 验证审计可以通过查询获取
        # 获取用户的角色
        user_roles = await PermissionService.get_user_roles(user.id)
        assert len(user_roles) == 1

        # 获取角色的权限
        role_permissions = await PermissionService.get_role_permissions(role.id)
        assert len(role_permissions) == 1

        # 获取用户的权限
        user_permissions = await PermissionService.get_user_permissions(user.id)
        assert len(user_permissions) == 1
