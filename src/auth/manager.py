from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, IntegerIDMixin
from sqlalchemy import select

from src.core.config import Settings, get_settings
from src.core.schemas import Role, User, UserRole

from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.schemas import OAuthAccount
from src.session import get_session


async def get_user_db(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    def __init__(self, user_db, settings: Settings):
        super().__init__(user_db)
        self.settings = settings

    @property
    def reset_password_token_secret(self):
        return self.settings.auth.jwt_secret

    @property
    def verification_token_secret(self):
        return self.settings.auth.jwt_secret

    async def on_after_register(
        self, user: User, request: Request | None = None
    ) -> None:
        if not self.settings.auth.rbac_enabled:
            return

        default_role = self.settings.auth.default_user_role
        if not default_role:
            return

        result = await self.user_db.session.execute(
            select(Role).where(Role.name == default_role)
        )
        role = result.scalar_one_or_none()
        if not role:
            return

        self.user_db.session.add(UserRole(user_id=user.id, role_id=role.id))
        await self.user_db.session.commit()

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ) -> None:
        pass

    async def on_after_reset_password(
        self, user: User, request: Request | None = None
    ) -> None:
        from src.cache import cache

        from .backend import RefreshTokenManager

        refresh_manager = RefreshTokenManager(cache, self.settings)
        await refresh_manager.revoke_all_user_tokens(user.id)


async def get_user_manager(
    user_db=Depends(get_user_db),
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db, settings)
