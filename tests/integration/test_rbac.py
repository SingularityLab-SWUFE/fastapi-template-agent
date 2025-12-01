"""RBAC 权限系统集成测试

测试角色权限分配和检查的完整流程。
"""

import pytest
from datetime import datetime, timezone
from sqlmodel import select

from src.core.schemas.user import User, UserRole
from src.core.schemas.role import Role, Permission, RolePermission


class TestRBACIntegration:
    """RBAC 权限系统集成测试套件"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_assign_role_to_user(self, db_session, test_user, test_role):
        """测试为用户分配角色"""
        # 初始状态：用户没有角色
        result = await db_session.exec(
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == test_user.id)
        )
        user_roles = result.all()
        assert len(user_roles) == 0

        # 分配角色
        user_role = UserRole(user_id=test_user.id, role_id=test_role.id)
        db_session.add(user_role)
        await db_session.commit()

        # 验证用户拥有该角色
        result = await db_session.exec(
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == test_user.id)
        )
        user_roles = result.all()
        assert len(user_roles) == 1
        assert user_roles[0].id == test_role.id
        assert user_roles[0].name == test_role.name

        # 验证数据库中的关联记录
        result = await db_session.exec(
            select(UserRole).where(
                UserRole.user_id == test_user.id,
                UserRole.role_id == test_role.id,
            )
        )
        user_role = result.first()
        assert user_role is not None
        assert user_role.user_id == test_user.id
        assert user_role.role_id == test_role.id

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_remove_role_from_user(self, db_session, test_user, test_role):
        """测试从用户移除角色"""
        # 创建用户角色关联
        user_role = UserRole(user_id=test_user.id, role_id=test_role.id)
        db_session.add(user_role)
        await db_session.commit()

        # 验证已分配
        result = await db_session.exec(
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == test_user.id)
        )
        user_roles = result.all()
        assert len(user_roles) == 1

        # 移除角色
        result = await db_session.exec(
            select(UserRole).where(
                UserRole.user_id == test_user.id,
                UserRole.role_id == test_role.id,
            )
        )
        user_role = result.first()
        assert user_role is not None
        await db_session.delete(user_role)
        await db_session.commit()

        # 验证角色已移除
        result = await db_session.exec(
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == test_user.id)
        )
        user_roles = result.all()
        assert len(user_roles) == 0

        # 验证数据库中的关联记录已删除
        result = await db_session.exec(
            select(UserRole).where(
                UserRole.user_id == test_user.id,
                UserRole.role_id == test_role.id,
            )
        )
        user_role = result.first()
        assert user_role is None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_assign_permission_to_role(self, db_session, test_role, test_permission):
        """测试为角色分配权限"""
        # 初始状态：角色没有权限
        result = await db_session.exec(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id == test_role.id)
        )
        role_permissions = result.all()
        assert len(role_permissions) == 0

        # 分配权限
        role_permission = RolePermission(
            role_id=test_role.id, permission_id=test_permission.id
        )
        db_session.add(role_permission)
        await db_session.commit()

        # 验证角色拥有该权限
        result = await db_session.exec(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id == test_role.id)
        )
        role_permissions = result.all()
        assert len(role_permissions) == 1
        assert role_permissions[0].id == test_permission.id
        assert role_permissions[0].code == test_permission.code

        # 验证数据库中的关联记录
        result = await db_session.exec(
            select(RolePermission).where(
                RolePermission.role_id == test_role.id,
                RolePermission.permission_id == test_permission.id,
            )
        )
        role_permission = result.first()
        assert role_permission is not None
        assert role_permission.role_id == test_role.id
        assert role_permission.permission_id == test_permission.id

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_remove_permission_from_role(
        self, db_session, test_role, test_permission
    ):
        """测试从角色移除权限"""
        # 创建角色权限关联
        role_permission = RolePermission(
            role_id=test_role.id, permission_id=test_permission.id
        )
        db_session.add(role_permission)
        await db_session.commit()

        # 验证已分配
        result = await db_session.exec(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id == test_role.id)
        )
        role_permissions = result.all()
        assert len(role_permissions) == 1

        # 移除权限
        result = await db_session.exec(
            select(RolePermission).where(
                RolePermission.role_id == test_role.id,
                RolePermission.permission_id == test_permission.id,
            )
        )
        role_permission = result.first()
        assert role_permission is not None
        await db_session.delete(role_permission)
        await db_session.commit()

        # 验证权限已移除
        result = await db_session.exec(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id == test_role.id)
        )
        role_permissions = result.all()
        assert len(role_permissions) == 0

        # 验证数据库中的关联记录已删除
        result = await db_session.exec(
            select(RolePermission).where(
                RolePermission.role_id == test_role.id,
                RolePermission.permission_id == test_permission.id,
            )
        )
        role_permission = result.first()
        assert role_permission is None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_user_has_required_role(
        self, db_session, test_user, test_role
    ):
        """测试用户是否拥有必需的角色"""
        # 用户没有角色
        assert not await self._user_has_role(db_session, test_user.id, test_role.name)

        # 分配角色
        user_role = UserRole(user_id=test_user.id, role_id=test_role.id)
        db_session.add(user_role)
        await db_session.commit()

        # 用户现在有角色
        assert await self._user_has_role(db_session, test_user.id, test_role.name)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_user_lacks_required_role(
        self, db_session, test_user, test_role
    ):
        """测试用户缺少必需角色的情况"""
        # 用户没有该角色
        assert not await self._user_has_role(db_session, test_user.id, test_role.name)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_user_roles(self, db_session, test_user, test_role):
        """测试获取用户的所有角色"""
        # 初始状态：用户没有角色
        user_roles = await self._get_user_roles(db_session, test_user.id)
        assert len(user_roles) == 0

        # 分配一个角色
        user_role = UserRole(user_id=test_user.id, role_id=test_role.id)
        db_session.add(user_role)
        await db_session.commit()

        # 获取用户角色
        user_roles = await self._get_user_roles(db_session, test_user.id)
        assert len(user_roles) == 1
        assert user_roles[0]["name"] == test_role.name

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_role_permissions(self, db_session, test_role, test_permission):
        """测试获取角色的所有权限"""
        # 初始状态：角色没有权限
        role_permissions = await self._get_role_permissions(db_session, test_role.id)
        assert len(role_permissions) == 0

        # 分配一个权限
        role_permission = RolePermission(
            role_id=test_role.id, permission_id=test_permission.id
        )
        db_session.add(role_permission)
        await db_session.commit()

        # 获取角色权限
        role_permissions = await self._get_role_permissions(db_session, test_role.id)
        assert len(role_permissions) == 1
        assert role_permissions[0]["code"] == test_permission.code

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_user_has_required_permission(
        self, db_session, test_user, test_role, test_permission
    ):
        """测试用户是否拥有必需的权限"""
        # 创建角色和权限关联
        role_permission = RolePermission(
            role_id=test_role.id, permission_id=test_permission.id
        )
        db_session.add(role_permission)
        await db_session.commit()

        # 分配角色给用户
        user_role = UserRole(user_id=test_user.id, role_id=test_role.id)
        db_session.add(user_role)
        await db_session.commit()

        # 用户应该有权限
        assert await self._user_has_permission(
            db_session, test_user.id, test_permission.code
        )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_permission_flow(
        self, db_session, test_user, test_role, test_permission
    ):
        """测试完整的权限流程：创建角色→分配权限→分配给用户→验证权限"""
        # 1. 创建角色和权限
        assert test_role.id is not None
        assert test_permission.id is not None

        # 2. 为角色分配权限
        role_permission = RolePermission(
            role_id=test_role.id, permission_id=test_permission.id
        )
        db_session.add(role_permission)
        await db_session.commit()

        # 3. 为用户分配角色
        user_role = UserRole(user_id=test_user.id, role_id=test_role.id)
        db_session.add(user_role)
        await db_session.commit()

        # 4. 验证用户权限
        has_permission = await self._user_has_permission(
            db_session, test_user.id, test_permission.code
        )
        assert has_permission

    async def _user_has_role(self, db_session, user_id: int, role_name: str) -> bool:
        """检查用户是否有特定角色"""
        result = await db_session.exec(
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id, Role.name == role_name)
        )
        role = result.first()
        return role is not None

    async def _get_user_roles(self, db_session, user_id: int) -> list[dict]:
        """获取用户的所有角色"""
        result = await db_session.exec(
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        roles = result.all()
        return [{"id": r.id, "name": r.name} for r in roles]

    async def _get_role_permissions(self, db_session, role_id: int) -> list[dict]:
        """获取角色的所有权限"""
        result = await db_session.exec(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .where(RolePermission.role_id == role_id)
        )
        permissions = result.all()
        return [{"id": p.id, "code": p.code} for p in permissions]

    async def _user_has_permission(
        self, db_session, user_id: int, permission_code: str
    ) -> bool:
        """检查用户是否有特定权限"""
        result = await db_session.exec(
            select(Permission)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(UserRole, RolePermission.role_id == UserRole.role_id)
            .where(
                UserRole.user_id == user_id,
                Permission.code == permission_code,
            )
        )
        permission = result.first()
        return permission is not None
