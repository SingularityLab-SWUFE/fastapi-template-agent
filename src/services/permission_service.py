"""权限管理服务

提供用户角色和权限的查询、分配、撤销等业务逻辑。
"""

from typing import List, Optional
from sqlmodel import select

from src.core.schemas.user import User, UserRole
from src.core.schemas.role import Role, Permission, RolePermission
from src.session import get_session


class PermissionService:
    """权限管理服务"""

    @staticmethod
    async def get_user_roles(user_id: int) -> List[Role]:
        """获取用户的所有角色

        Args:
            user_id: 用户 ID

        Returns:
            角色对象列表
        """
        async with get_session() as session:
            result = await session.exec(
                select(Role)
                .join(UserRole, Role.id == UserRole.role_id)
                .where(UserRole.user_id == user_id)
            )
            return result.all()

    @staticmethod
    async def get_user_role_names(user_id: int) -> List[str]:
        """获取用户的所有角色名称

        Args:
            user_id: 用户 ID

        Returns:
            角色名称列表
        """
        roles = await PermissionService.get_user_roles(user_id)
        return [role.name for role in roles]

    @staticmethod
    async def get_user_permissions(user_id: int) -> List[Permission]:
        """获取用户的所有权限

        Args:
            user_id: 用户 ID

        Returns:
            权限对象列表
        """
        async with get_session() as session:
            result = await session.exec(
                select(Permission)
                .join(
                    RolePermission,
                    Permission.id == RolePermission.permission_id,
                )
                .join(
                    UserRole,
                    RolePermission.role_id == UserRole.role_id,
                )
                .where(UserRole.user_id == user_id)
            )
            return result.all()

    @staticmethod
    async def get_user_permission_codes(user_id: int) -> List[str]:
        """获取用户的所有权限代码

        Args:
            user_id: 用户 ID

        Returns:
            权限代码列表
        """
        permissions = await PermissionService.get_user_permissions(user_id)
        return [perm.code for perm in permissions]

    @staticmethod
    async def assign_role_to_user(user_id: int, role_id: int) -> bool:
        """为用户分配角色

        Args:
            user_id: 用户 ID
            role_id: 角色 ID

        Returns:
            分配是否成功（如果已存在则返回 False）
        """
        async with get_session() as session:
            # 检查是否已存在
            existing = await session.exec(
                select(UserRole).where(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id,
                )
            )
            if existing.first():
                return False

            user_role = UserRole(user_id=user_id, role_id=role_id)
            session.add(user_role)
            await session.commit()
            return True

    @staticmethod
    async def remove_role_from_user(user_id: int, role_id: int) -> bool:
        """从用户移除角色

        Args:
            user_id: 用户 ID
            role_id: 角色 ID

        Returns:
            移除是否成功（如果不存在则返回 False）
        """
        async with get_session() as session:
            result = await session.exec(
                select(UserRole).where(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id,
                )
            )
            user_role = result.first()
            if not user_role:
                return False

            await session.delete(user_role)
            await session.commit()
            return True

    @staticmethod
    async def assign_permission_to_role(role_id: int, permission_id: int) -> bool:
        """为角色分配权限

        Args:
            role_id: 角色 ID
            permission_id: 权限 ID

        Returns:
            分配是否成功（如果已存在则返回 False）
        """
        async with get_session() as session:
            # 检查是否已存在
            existing = await session.exec(
                select(RolePermission).where(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id,
                )
            )
            if existing.first():
                return False

            role_permission = RolePermission(
                role_id=role_id, permission_id=permission_id
            )
            session.add(role_permission)
            await session.commit()
            return True

    @staticmethod
    async def remove_permission_from_role(role_id: int, permission_id: int) -> bool:
        """从角色移除权限

        Args:
            role_id: 角色 ID
            permission_id: 权限 ID

        Returns:
            移除是否成功（如果不存在则返回 False）
        """
        async with get_session() as session:
            result = await session.exec(
                select(RolePermission).where(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id,
                )
            )
            role_permission = result.first()
            if not role_permission:
                return False

            await session.delete(role_permission)
            await session.commit()
            return True

    @staticmethod
    async def check_user_has_role(user_id: int, role_name: str) -> bool:
        """检查用户是否拥有指定角色

        Args:
            user_id: 用户 ID
            role_name: 角色名称

        Returns:
            是否拥有角色
        """
        async with get_session() as session:
            result = await session.exec(
                select(Role)
                .join(UserRole, Role.id == UserRole.role_id)
                .where(
                    UserRole.user_id == user_id,
                    Role.name == role_name,
                )
            )
            return result.first() is not None

    @staticmethod
    async def check_user_has_permission(user_id: int, permission_code: str) -> bool:
        """检查用户是否拥有指定权限

        Args:
            user_id: 用户 ID
            permission_code: 权限代码

        Returns:
            是否拥有权限
        """
        async with get_session() as session:
            result = await session.exec(
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
                    UserRole.user_id == user_id,
                    Permission.code == permission_code,
                )
            )
            return result.first() is not None

    @staticmethod
    async def create_role(name: str, description: Optional[str] = None) -> Role:
        """创建角色

        Args:
            name: 角色名称
            description: 角色描述

        Returns:
            创建的角色对象
        """
        async with get_session() as session:
            role = Role(name=name, description=description, is_system=False)
            session.add(role)
            await session.commit()
            await session.refresh(role)
            return role

    @staticmethod
    async def get_role_by_name(name: str) -> Optional[Role]:
        """根据名称获取角色

        Args:
            name: 角色名称

        Returns:
            角色对象，如果不存在则返回 None
        """
        async with get_session() as session:
            result = await session.exec(select(Role).where(Role.name == name))
            return result.first()

    @staticmethod
    async def get_all_roles() -> List[Role]:
        """获取所有角色

        Returns:
            角色对象列表
        """
        async with get_session() as session:
            result = await session.exec(select(Role))
            return result.all()

    @staticmethod
    async def get_role_permissions(role_id: int) -> List[Permission]:
        """获取角色的所有权限

        Args:
            role_id: 角色 ID

        Returns:
            权限对象列表
        """
        async with get_session() as session:
            result = await session.exec(
                select(Permission)
                .join(
                    RolePermission,
                    Permission.id == RolePermission.permission_id,
                )
                .where(RolePermission.role_id == role_id)
            )
            return result.all()

    @staticmethod
    async def get_all_permissions() -> List[Permission]:
        """获取所有权限

        Returns:
            权限对象列表
        """
        async with get_session() as session:
            result = await session.exec(select(Permission))
            return result.all()
