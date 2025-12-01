"""自定义用户管理器

独立实现的用户管理器，不依赖 fastapi-users。
"""

from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import Request
from sqlmodel import select

from src.core.schemas.user import User
from src.session import get_session


class UserManager:
    """自定义用户管理器"""

    def __init__(self):
        """初始化用户管理器"""
        pass

    async def create(
        self,
        username: str,
        email: str,
        password: str,
        request: Optional[Request] = None,
    ) -> User:
        """创建用户

        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            request: FastAPI 请求对象

        Returns:
            创建的用户

        Raises:
            ValueError: 用户已存在
        """
        # 检查用户是否已存在
        existing_user = await self.get_by_email(email)
        if existing_user:
            raise ValueError("用户已存在")

        # 哈希密码
        from src.auth.token_manager import TokenManager
        hashed_password = TokenManager.get_password_hash(password)

        # 创建用户
        db_user = User(
            username=username,
            hashed_password=hashed_password,
            email=email,
            is_active=True,
            is_superuser=False,
        )

        async with get_session() as session:
            session.add(db_user)
            await session.commit()
            await session.refresh(db_user)

        # 自动分配默认角色（user 角色）
        await self.assign_default_role(db_user.id)

        return db_user

    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户

        Args:
            username: 用户名

        Returns:
            用户对象，如果不存在则返回 None
        """
        async with get_session() as session:
            result = await session.exec(select(User).where(User.username == username))
            return result.first()

    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户

        Args:
            email: 邮箱地址

        Returns:
            用户对象，如果不存在则返回 None
        """
        async with get_session() as session:
            result = await session.exec(select(User).where(User.email == email))
            return result.first()

    async def authenticate(
        self,
        username_or_email: str,
        password: str,
    ) -> Optional[User]:
        """用户认证

        Args:
            username_or_email: 用户名或邮箱
            password: 密码

        Returns:
            认证成功返回用户对象，失败返回 None
        """
        # 先尝试用户名
        user = await self.get_by_username(username_or_email)

        # 再尝试邮箱
        if not user:
            user = await self.get_by_email(username_or_email)

        if not user:
            return None

        if not user.is_active:
            return None

        # 验证密码
        from src.auth.token_manager import TokenManager
        verified = TokenManager.verify_password(password, user.hashed_password)
        if not verified:
            return None

        return user

    async def assign_default_role(self, user_id: int) -> None:
        """为用户分配默认角色（user 角色）

        Args:
            user_id: 用户 ID
        """
        from src.core.schemas.role import Role
        from src.core.schemas.user import UserRole

        async with get_session() as session:
            # 查询 user 角色
            result = await session.exec(
                select(Role).where(Role.name == "user")
            )
            user_role = result.first()

            if user_role:
                # 检查用户是否已有该角色
                existing = await session.exec(
                    select(UserRole).where(
                        UserRole.user_id == user_id,
                        UserRole.role_id == user_role.id,
                    )
                )
                if not existing.first():
                    # 分配角色
                    user_role_assignment = UserRole(
                        user_id=user_id, role_id=user_role.id
                    )
                    session.add(user_role_assignment)
                    await session.commit()

    async def assign_role(self, user_id: int, role_id: int) -> None:
        """为用户分配角色

        Args:
            user_id: 用户 ID
            role_id: 角色 ID
        """
        from src.core.schemas.user import UserRole

        async with get_session() as session:
            # 检查是否已存在
            existing = await session.exec(
                select(UserRole).where(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id,
                )
            )
            if not existing.first():
                user_role = UserRole(user_id=user_id, role_id=role_id)
                session.add(user_role)
                await session.commit()

    async def remove_role(self, user_id: int, role_id: int) -> None:
        """移除用户角色

        Args:
            user_id: 用户 ID
            role_id: 角色 ID
        """
        from src.core.schemas.user import UserRole

        async with get_session() as session:
            result = await session.exec(
                select(UserRole).where(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id,
                )
            )
            user_role = result.first()
            if user_role:
                await session.delete(user_role)
                await session.commit()

    async def get_user_roles(self, user_id: int) -> list[str]:
        """获取用户的所有角色

        Args:
            user_id: 用户 ID

        Returns:
            角色名称列表
        """
        from src.core.schemas.role import Role
        from src.core.schemas.user import UserRole

        async with get_session() as session:
            result = await session.exec(
                select(Role.name)
                .join(UserRole, Role.id == UserRole.role_id)
                .where(UserRole.user_id == user_id)
            )
            return result.all()

    async def is_superuser(self, user: User) -> bool:
        """检查用户是否为超级用户

        Args:
            user: 用户对象

        Returns:
            是否为超级用户
        """
        return user.is_superuser

    async def is_active(self, user: User) -> bool:
        """检查用户是否活跃

        Args:
            user: 用户对象

        Returns:
            是否活跃
        """
        return user.is_active
