from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, IntegerIDMixin

from src.core.config import get_settings
from src.core.schemas import User

from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.schemas import OAuthAccount
from src.session import get_session


async def get_user_db(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    def __init__(self, user_db):
        super().__init__(user_db)
        self._settings = None

    def _get_settings(self):
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    @property
    def reset_password_token_secret(self):
        return self._get_settings().auth.jwt_secret

    @property
    def verification_token_secret(self):
        return self._get_settings().auth.jwt_secret

    async def on_after_register(
        self, user: User, request: Request | None = None
    ) -> None:
        pass

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ) -> None:
        pass

    async def on_after_reset_password(
        self, user: User, request: Request | None = None
    ) -> None:
        from src.cache import cache

        from .backend import RefreshTokenManager

        refresh_manager = RefreshTokenManager(cache)
        await refresh_manager.revoke_all_user_tokens(user.id)


async def get_user_manager(
    user_db=Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)
