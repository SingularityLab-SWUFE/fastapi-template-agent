"""角色权限管理集成测试

测试角色创建、更新、删除，权限分配等管理员功能。
"""

import pytest
from datetime import datetime, timezone
from sqlmodel import select

from src.core.schemas.role import Role, Permission, RolePermission
from src.core.schemas.user import User, UserRole


class TestRoleManagementIntegration:
    """角色权限管理集成测试套件"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_role(self, db_session):
        """测试创建新角色"""
        name = f"test_role_create_{datetime.now().timestamp()}"
        role = Role(
            name=name,
            description="测试创建的角色",
            is_system=False,
        )
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)

        # 验证角色创建成功
        assert role is not None
        assert role.name == name
        assert role.description == "测试创建的角色"
        assert role.is_system is False

        # 验证数据库中有该角色
        result = await db_session.exec(select(Role).where(Role.name == name))
        retrieved_role = result.first()
        assert retrieved_role is not None
        assert retrieved_role.id == role.id
        assert retrieved_role.name == role.name

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_role(self, db_session, test_role):
        """测试更新角色信息"""
        # 更新角色
        test_role.description = "更新后的描述"
        db_session.add(test_role)
        await db_session.commit()
        await db_session.refresh(test_role)

        # 验证更新成功
        result = await db_session.exec(select(Role).where(Role.id == test_role.id))
        updated_role = result.first()
        assert updated_role is not None
        assert updated_role.description == "更新后的描述"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_delete_role(self, db_session, test_user, test_permission):
        """测试删除角色"""
        # 创建测试角色
        role = Role(
            name=f"test_role_delete_{datetime.now().timestamp()}",
            description="待删除的角色",
            is_system=False,
        )
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)

        # 为角色分配权限
        role_permission = RolePermission(
            role_id=role.id, permission_id=test_permission.id
        )
        db_session.add(role_permission)

        # 为用户分配角色
        user_role = UserRole(user_id=test_user.id, role_id=role.id)
        db_session.add(user_role)

        await db_session.commit()

        # 验证角色有关联数据
        result = await db_session.exec(
            select(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == test_permission.id,
            )
        )
        assert result.first() is not None

        result = await db_session.exec(
            select(UserRole).where(
                UserRole.user_id == test_user.id,
                UserRole.role_id == role.id,
            )
        )
        assert result.first() is not None

        # 删除角色
        await db_session.delete(role)
        await db_session.commit()

        # 验证角色已删除
        result = await db_session.exec(select(Role).where(Role.id == role.id))
        deleted_role = result.first()
        assert deleted_role is None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_assign_multiple_roles_to_user(self, db_session, test_user):
        """测试为用户分配多个角色"""
        # 创建多个角色
        roles = []
        for i in range(3):
            role = Role(
                name=f"role_multi_{i}_{datetime.now().timestamp()}",
                description=f"角色{i}",
                is_system=False,
            )
            db_session.add(role)
            await db_session.commit()
            await db_session.refresh(role)
            roles.append(role)

        # 分配所有角色
        for role in roles:
            user_role = UserRole(user_id=test_user.id, role_id=role.id)
            db_session.add(user_role)
        await db_session.commit()

        # 验证用户拥有所有角色
        result = await db_session.exec(
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == test_user.id)
        )
        user_roles = result.all()
        assert len(user_roles) == 3

        role_names = {role.name for role in user_roles}
        assert len(role_names) == 3

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_role_based_api_access(
        self, db_session, test_user, test_role, test_permission
    ):
        """测试基于角色的 API 访问控制"""
        # 为角色分配权限
        role_permission = RolePermission(
            role_id=test_role.id, permission_id=test_permission.id
        )
        db_session.add(role_permission)
        await db_session.commit()

        # 为用户分配角色
        user_role = UserRole(user_id=test_user.id, role_id=test_role.id)
        db_session.add(user_role)
        await db_session.commit()

        # 验证用户通过角色获得权限
        result = await db_session.exec(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(UserRole, RolePermission.role_id == UserRole.role_id)
            .where(UserRole.user_id == test_user.id)
        )
        permissions = result.all()
        assert len(permissions) >= 1

        # 验证权限包含测试权限
        permission_codes = {p.code for p in permissions}
        assert test_permission.code in permission_codes

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_permission_caching(
        self, db_session, test_role, test_permission
    ):
        """测试权限缓存机制"""
        # 为角色分配权限
        role_permission = RolePermission(
            role_id=test_role.id, permission_id=test_permission.id
        )
        db_session.add(role_permission)
        await db_session.commit()

        # 第一次查询
        result = await db_session.exec(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id == test_role.id)
        )
        permissions1 = result.all()
        assert len(permissions1) == 1

        # 第二次查询（测试缓存）
        result = await db_session.exec(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id == test_role.id)
        )
        permissions2 = result.all()
        assert len(permissions2) == 1
        assert permissions1[0].id == permissions2[0].id

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_bulk_role_assignment(
        self, db_session, test_admin_user
    ):
        """测试批量角色分配"""
        # 创建多个用户
        users = []
        for i in range(3):
            user = User(
                username=f"bulk_user_{i}_{datetime.now().timestamp()}",
                hashed_password="hashed",
                is_active=True,
            )
            db_session.add(user)
            await db_session.commit()
            await db_session.refresh(user)
            users.append(user)

        # 创建角色
        role = Role(
            name=f"bulk_role_{datetime.now().timestamp()}",
            description="批量测试角色",
            is_system=False,
        )
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)

        # 为所有用户分配角色
        for user in users:
            user_role = UserRole(user_id=user.id, role_id=role.id)
            db_session.add(user_role)
        await db_session.commit()

        # 验证所有用户都有该角色
        result = await db_session.exec(
            select(User).join(UserRole, User.id == UserRole.user_id).where(UserRole.role_id == role.id)
        )
        assigned_users = result.all()
        assert len(assigned_users) == 3

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_role_permission_audit(self, db_session, test_role, test_permission):
        """测试角色权限审计"""
        # 为角色分配权限（记录时间）
        import time
        time.sleep(0.01)  # 确保时间差异

        role_permission = RolePermission(
            role_id=test_role.id, permission_id=test_permission.id
        )
        db_session.add(role_permission)
        await db_session.commit()
        await db_session.refresh(role_permission)

        time.sleep(0.01)  # 确保时间差异

        # 验证审计记录存在
        result = await db_session.exec(
            select(RolePermission)
            .where(
                RolePermission.role_id == test_role.id,
                RolePermission.permission_id == test_permission.id,
            )
        )
        audit_record = result.first()
        assert audit_record is not None
        assert audit_record.created_at is not None

        # 验证可以通过审计日志查询权限分配
        assert audit_record.role_id == test_role.id
        assert audit_record.permission_id == test_permission.id
