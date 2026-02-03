from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, IntegerIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import OAuthAccount, User
from src.config import Settings, get_settings
from src.session import get_session

from .backend import RefreshTokenManager, get_refresh_token_manager


async def get_user_db(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    def __init__(
        self, user_db, settings: Settings, refresh_manager: RefreshTokenManager
    ):
        super().__init__(user_db)
        self.settings = settings
        self.refresh_manager = refresh_manager

    @property
    def reset_password_token_secret(self):
        return self.settings.auth.jwt_secret

    @property
    def verification_token_secret(self):
        return self.settings.auth.jwt_secret

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
        await self.refresh_manager.revoke_all_user_tokens(user.id)


async def get_user_manager(
    user_db=Depends(get_user_db),
    settings: Settings = Depends(get_settings),
    refresh_manager: RefreshTokenManager = Depends(get_refresh_token_manager),
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db, settings, refresh_manager)
