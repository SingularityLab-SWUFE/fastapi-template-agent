"""RBAC 权限系统集成测试

测试角色权限分配和检查的完整流程。
"""

import pytest
from datetime import datetime, timezone
from sqlmodel import select, SQLModel, create_engine
from sqlalchemy import text
import os

from src.core.schemas.user import User, UserRole
from src.core.schemas.role import Role, Permission, RolePermission


@pytest.mark.usefixtures("test_db")
class TestRBACIntegration:
    """RBAC 权限系统集成测试套件"""

    @pytest.fixture(scope="class")
    async def test_db(self):
        """初始化测试数据库"""
        # 使用 SQLite 文件数据库进行测试
        db_url = "sqlite+aiosqlite:///./test.db"

        # 初始化数据库连接
        from src.session import init_db, close_db
        await init_db(db_url, echo=False)

        # 创建所有表 - 使用同步方式
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

    @pytest.fixture
    async def test_session(self, test_db):
        """创建测试数据会话"""
        from src.session import async_session_factory
        async with async_session_factory() as session:
            yield session
            # 每个测试后回滚
            try:
                await session.rollback()
            except Exception:
                pass

    @pytest.mark.asyncio
    async def test_assign_role_to_user(self):
        """测试为用户分配角色"""
        from src.core.schemas.user import User, UserRole
        from src.core.schemas.role import Role
        from src.session import get_session

        async with get_session() as session:
            # 创建测试用户和角色
            user = User(
                username="testuser",
                hashed_password="hashed_password",
                is_active=True,
                is_superuser=False,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            role = Role(
                name="test_role",
                description="测试角色",
                is_system=False,
            )
            session.add(role)
            await session.commit()
            await session.refresh(role)

            # 初始状态：用户没有角色
            result = await session.exec(
                select(Role)
                .join(UserRole, Role.id == UserRole.role_id)
                .where(UserRole.user_id == user.id)
            )
            user_roles = result.all()
            assert len(user_roles) == 0

            # 分配角色
            user_role = UserRole(user_id=user.id, role_id=role.id)
            session.add(user_role)
            await session.commit()

            # 验证用户拥有该角色
            result = await session.exec(
                select(Role)
                .join(UserRole, Role.id == UserRole.role_id)
                .where(UserRole.user_id == user.id)
            )
            user_roles = result.all()
            assert len(user_roles) == 1
            assert user_roles[0].id == role.id
            assert user_roles[0].name == "test_role"

            # 验证数据库中的关联记录
            result = await session.exec(
                select(UserRole).where(
                    UserRole.user_id == user.id,
                    UserRole.role_id == role.id,
                )
            )
            user_role = result.first()
            assert user_role is not None
            assert user_role.user_id == user.id
            assert user_role.role_id == role.id

    @pytest.mark.asyncio
    async def test_remove_role_from_user(self, test_session):
        """测试从用户移除角色"""
        from src.core.schemas.user import User, UserRole
        from src.core.schemas.role import Role

        # 创建测试用户和角色
        user = User(
            username="testuser2",
            hashed_password="hashed_password",
            is_active=True,
            is_superuser=False,
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        role = Role(
            name="test_role2",
            description="测试角色2",
            is_system=False,
        )
        test_session.add(role)
        await test_session.commit()
        await test_session.refresh(role)

        # 分配角色
        user_role = UserRole(user_id=user.id, role_id=role.id)
        test_session.add(user_role)
        await test_session.commit()

        # 验证已分配
        result = await test_session.exec(
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user.id)
        )
        user_roles = result.all()
        assert len(user_roles) == 1

        # 移除角色
        result = await test_session.exec(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id,
            )
        )
        user_role = result.first()
        assert user_role is not None
        await test_session.delete(user_role)
        await test_session.commit()

        # 验证角色已移除
        result = await test_session.exec(
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user.id)
        )
        user_roles = result.all()
        assert len(user_roles) == 0

        # 验证数据库中的关联记录已删除
        result = await test_session.exec(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id,
            )
        )
        user_role = result.first()
        assert user_role is None

    @pytest.mark.asyncio
    async def test_assign_permission_to_role(self, test_session):
        """测试为角色分配权限"""
        from src.core.schemas.role import Role, Permission

        # 创建测试角色和权限
        role = Role(
            name="test_role3",
            description="测试角色3",
            is_system=False,
        )
        test_session.add(role)
        await test_session.commit()
        await test_session.refresh(role)

        permission = Permission(
            name="测试权限",
            code="test.permission",
            description="测试权限",
        )
        test_session.add(permission)
        await test_session.commit()
        await test_session.refresh(permission)

        # 初始状态：角色没有权限
        result = await test_session.exec(
            select(Permission)
            .join(
                RolePermission,
                Permission.id == RolePermission.permission_id,
            )
            .where(RolePermission.role_id == role.id)
        )
        permissions = result.all()
        assert len(permissions) == 0

        # 分配权限
        role_permission = RolePermission(role_id=role.id, permission_id=permission.id)
        test_session.add(role_permission)
        await test_session.commit()

        # 验证角色拥有该权限
        result = await test_session.exec(
            select(Permission)
            .join(
                RolePermission,
                Permission.id == RolePermission.permission_id,
            )
            .where(RolePermission.role_id == role.id)
        )
        permissions = result.all()
        assert len(permissions) == 1
        assert permissions[0].id == permission.id
        assert permissions[0].code == "test.permission"

        # 验证数据库中的关联记录
        result = await test_session.exec(
            select(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == permission.id,
            )
        )
        role_permission = result.first()
        assert role_permission is not None
        assert role_permission.role_id == role.id
        assert role_permission.permission_id == permission.id

    @pytest.mark.asyncio
    async def test_remove_permission_from_role(self, test_session):
        """测试从角色移除权限"""
        from src.core.schemas.role import Role, Permission, RolePermission

        # 创建测试角色和权限
        role = Role(
            name="test_role4",
            description="测试角色4",
            is_system=False,
        )
        test_session.add(role)
        await test_session.commit()
        await test_session.refresh(role)

        permission = Permission(
            name="测试权限4",
            code="test.permission4",
            description="测试权限4",
        )
        test_session.add(permission)
        await test_session.commit()
        await test_session.refresh(permission)

        # 分配权限
        role_permission = RolePermission(role_id=role.id, permission_id=permission.id)
        test_session.add(role_permission)
        await test_session.commit()

        # 验证已分配
        result = await test_session.exec(
            select(Permission)
            .join(
                RolePermission,
                Permission.id == RolePermission.permission_id,
            )
            .where(RolePermission.role_id == role.id)
        )
        permissions = result.all()
        assert len(permissions) == 1

        # 移除权限
        result = await test_session.exec(
            select(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == permission.id,
            )
        )
        role_permission = result.first()
        assert role_permission is not None
        await test_session.delete(role_permission)
        await test_session.commit()

        # 验证权限已移除
        result = await test_session.exec(
            select(Permission)
            .join(
                RolePermission,
                Permission.id == RolePermission.permission_id,
            )
            .where(RolePermission.role_id == role.id)
        )
        permissions = result.all()
        assert len(permissions) == 0

        # 验证数据库中的关联记录已删除
        result = await test_session.exec(
            select(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == permission.id,
            )
        )
        role_permission = result.first()
        assert role_permission is None

    @pytest.mark.asyncio
    async def test_user_has_required_role(self, test_session):
        """测试用户拥有必需角色"""
        from src.core.schemas.user import User, UserRole
        from src.core.schemas.role import Role

        # 创建测试用户和角色
        user = User(
            username="testuser3",
            hashed_password="hashed_password",
            is_active=True,
            is_superuser=False,
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        role = Role(
            name="test_role5",
            description="测试角色5",
            is_system=False,
        )
        test_session.add(role)
        await test_session.commit()
        await test_session.refresh(role)

        # 分配角色
        user_role = UserRole(user_id=user.id, role_id=role.id)
        test_session.add(user_role)
        await test_session.commit()

        # 验证用户拥有该角色
        result = await test_session.exec(
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(
                UserRole.user_id == user.id,
                Role.name == "test_role5",
            )
        )
        user_role = result.first()
        assert user_role is not None

        # 验证用户不拥有其他角色
        result = await test_session.exec(
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(
                UserRole.user_id == user.id,
                Role.name == "other_role",
            )
        )
        user_role = result.first()
        assert user_role is None

    @pytest.mark.asyncio
    async def test_user_lacks_required_role(self, test_session):
        """测试用户缺少必需角色"""
        from src.core.schemas.user import User

        # 创建测试用户但不分配角色
        user = User(
            username="testuser4",
            hashed_password="hashed_password",
            is_active=True,
            is_superuser=False,
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        # 验证用户没有角色
        result = await test_session.exec(
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user.id)
        )
        user_roles = result.all()
        assert len(user_roles) == 0

        # 验证用户不拥有任何角色
        result = await test_session.exec(
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(
                UserRole.user_id == user.id,
                Role.name == "any_role",
            )
        )
        user_role = result.first()
        assert user_role is None

    @pytest.mark.asyncio
    async def test_get_user_roles(self, test_session):
        """测试获取用户所有角色"""
        from src.core.schemas.user import User, UserRole
        from src.core.schemas.role import Role

        # 创建测试用户
        user = User(
            username="testuser5",
            hashed_password="hashed_password",
            is_active=True,
            is_superuser=False,
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        # 创建两个角色
        role1 = Role(
            name="test_role6",
            description="测试角色6",
            is_system=False,
        )
        test_session.add(role1)
        await test_session.commit()
        await test_session.refresh(role1)

        role2 = Role(
            name="test_role_7",
            description="测试角色7",
            is_system=False,
        )
        test_session.add(role2)
        await test_session.commit()
        await test_session.refresh(role2)

        # 分配两个角色
        user_role1 = UserRole(user_id=user.id, role_id=role1.id)
        test_session.add(user_role1)

        user_role2 = UserRole(user_id=user.id, role_id=role2.id)
        test_session.add(user_role2)

        await test_session.commit()

        # 获取用户所有角色
        result = await test_session.exec(
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user.id)
        )
        user_roles = result.all()
        assert len(user_roles) == 2

        # 验证角色信息
        role_names = {role.name for role in user_roles}
        assert "test_role6" in role_names
        assert "test_role_7" in role_names

        # 获取角色名称列表
        role_names_list = [role.name for role in user_roles]
        assert len(role_names_list) == 2
        assert "test_role6" in role_names_list
        assert "test_role_7" in role_names_list

    @pytest.mark.asyncio
    async def test_get_role_permissions(self, test_session):
        """测试获取角色所有权限"""
        from src.core.schemas.role import Role, Permission, RolePermission

        # 创建测试角色
        role = Role(
            name="test_role8",
            description="测试角色8",
            is_system=False,
        )
        test_session.add(role)
        await test_session.commit()
        await test_session.refresh(role)

        # 创建两个权限
        permission1 = Permission(
            name="测试权限8",
            code="test.permission8",
            description="测试权限8",
        )
        test_session.add(permission1)
        await test_session.commit()
        await test_session.refresh(permission1)

        permission2 = Permission(
            name="测试权限9",
            code="test.permission9",
            description="测试权限9",
        )
        test_session.add(permission2)
        await test_session.commit()
        await test_session.refresh(permission2)

        # 分配两个权限
        role_permission1 = RolePermission(role_id=role.id, permission_id=permission1.id)
        test_session.add(role_permission1)

        role_permission2 = RolePermission(role_id=role.id, permission_id=permission2.id)
        test_session.add(role_permission2)

        await test_session.commit()

        # 获取角色所有权限
        result = await test_session.exec(
            select(Permission)
            .join(
                RolePermission,
                Permission.id == RolePermission.permission_id,
            )
            .where(RolePermission.role_id == role.id)
        )
        permissions = result.all()
        assert len(permissions) == 2

        # 验证权限信息
        permission_codes = {perm.code for perm in permissions}
        assert "test.permission8" in permission_codes
        assert "test.permission9" in permission_codes

    @pytest.mark.asyncio
    async def test_user_has_required_permission(self, test_session):
        """测试用户拥有必需权限"""
        from src.core.schemas.user import User, UserRole
        from src.core.schemas.role import Role, Permission, RolePermission

        # 创建测试用户、角色和权限
        user = User(
            username="testuser6",
            hashed_password="hashed_password",
            is_active=True,
            is_superuser=False,
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        role = Role(
            name="test_role9",
            description="测试角色9",
            is_system=False,
        )
        test_session.add(role)
        await test_session.commit()
        await test_session.refresh(role)

        permission = Permission(
            name="测试权限10",
            code="test.permission10",
            description="测试权限10",
        )
        test_session.add(permission)
        await test_session.commit()
        await test_session.refresh(permission)

        # 为角色分配权限
        role_permission = RolePermission(role_id=role.id, permission_id=permission.id)
        test_session.add(role_permission)

        # 为用户分配角色
        user_role = UserRole(user_id=user.id, role_id=role.id)
        test_session.add(user_role)

        await test_session.commit()

        # 验证用户拥有该权限
        result = await test_session.exec(
            select(Permission)
            .join(
                RolePermission,
                Permission.id == RolePermission.permission_id,
            )
            .join(
                UserRole,
                RolePermission.role_id == UserRole.role_id,
            )
            .where(
                UserRole.user_id == user.id,
                Permission.code == "test.permission10",
            )
        )
        user_permission = result.first()
        assert user_permission is not None

        # 验证用户不拥有其他权限
        result = await test_session.exec(
            select(Permission)
            .join(
                RolePermission,
                Permission.id == RolePermission.permission_id,
            )
            .join(
                UserRole,
                RolePermission.role_id == UserRole.role_id,
            )
            .where(
                UserRole.user_id == user.id,
                Permission.code == "other.permission",
            )
        )
        user_permission = result.first()
        assert user_permission is None

        # 获取用户所有权限
        result = await test_session.exec(
            select(Permission)
            .join(
                RolePermission,
                Permission.id == RolePermission.permission_id,
            )
            .join(
                UserRole,
                RolePermission.role_id == UserRole.role_id,
            )
            .where(UserRole.user_id == user.id)
        )
        user_permissions = result.all()
        assert len(user_permissions) == 1
        assert user_permissions[0].code == "test.permission10"

        # 获取用户所有权限代码
        permission_codes = [perm.code for perm in user_permissions]
        assert len(permission_codes) == 1
        assert "test.permission10" in permission_codes

    @pytest.mark.asyncio
    async def test_full_permission_flow(self, test_session):
        """测试完整的权限分配流程：角色->权限->用户"""
        from src.core.schemas.user import User, UserRole
        from src.core.schemas.role import Role, Permission, RolePermission

        # 1. 创建用户、角色和权限
        user = User(
            username="testuser7",
            hashed_password="hashed_password",
            is_active=True,
            is_superuser=False,
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        admin_role = Role(
            name="admin",
            description="管理员角色",
            is_system=False,
        )
        test_session.add(admin_role)
        await test_session.commit()
        await test_session.refresh(admin_role)

        user_create_perm = Permission(
            name="创建用户",
            code="user.create",
            description="创建用户权限",
        )
        test_session.add(user_create_perm)
        await test_session.commit()
        await test_session.refresh(user_create_perm)

        user_delete_perm = Permission(
            name="删除用户",
            code="user.delete",
            description="删除用户权限",
        )
        test_session.add(user_delete_perm)
        await test_session.commit()
        await test_session.refresh(user_delete_perm)

        # 2. 为角色分配权限
        role_permission1 = RolePermission(
            role_id=admin_role.id, permission_id=user_create_perm.id
        )
        test_session.add(role_permission1)

        role_permission2 = RolePermission(
            role_id=admin_role.id, permission_id=user_delete_perm.id
        )
        test_session.add(role_permission2)

        await test_session.commit()

        # 验证角色拥有权限
        result = await test_session.exec(
            select(Permission)
            .join(
                RolePermission,
                Permission.id == RolePermission.permission_id,
            )
            .where(RolePermission.role_id == admin_role.id)
        )
        role_permissions = result.all()
        assert len(role_permissions) == 2

        # 3. 为用户分配角色
        user_role = UserRole(user_id=user.id, role_id=admin_role.id)
        test_session.add(user_role)

        await test_session.commit()

        # 4. 验证用户继承角色权限
        result = await test_session.exec(
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user.id)
        )
        user_roles = result.all()
        assert len(user_roles) == 1
        assert user_roles[0].name == "admin"

        result = await test_session.exec(
            select(Permission)
            .join(
                RolePermission,
                Permission.id == RolePermission.permission_id,
            )
            .join(
                UserRole,
                RolePermission.role_id == UserRole.role_id,
            )
            .where(UserRole.user_id == user.id)
        )
        user_permissions = result.all()
        assert len(user_permissions) == 2

        permission_codes = [perm.code for perm in user_permissions]
        assert "user.create" in permission_codes
        assert "user.delete" in permission_codes

        # 5. 验证权限检查
        # 检查 user.create 权限
        result = await test_session.exec(
            select(Permission)
            .join(
                RolePermission,
                Permission.id == RolePermission.permission_id,
            )
            .join(
                UserRole,
                RolePermission.role_id == UserRole.role_id,
            )
            .where(
                UserRole.user_id == user.id,
                Permission.code == "user.create",
            )
        )
        assert result.first() is not None

        # 检查 user.delete 权限
        result = await test_session.exec(
            select(Permission)
            .join(
                RolePermission,
                Permission.id == RolePermission.permission_id,
            )
            .join(
                UserRole,
                RolePermission.role_id == UserRole.role_id,
            )
            .where(
                UserRole.user_id == user.id,
                Permission.code == "user.delete",
            )
        )
        assert result.first() is not None

        # 检查不存在的权限
        result = await test_session.exec(
            select(Permission)
            .join(
                RolePermission,
                Permission.id == RolePermission.permission_id,
            )
            .join(
                UserRole,
                RolePermission.role_id == UserRole.role_id,
            )
            .where(
                UserRole.user_id == user.id,
                Permission.code == "user.update",
            )
        )
        assert result.first() is None
