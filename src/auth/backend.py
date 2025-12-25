"""Auth backend defining JWT strategy + refresh token management."""

import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import Depends
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from src.cache import CacheProtocol, get_cache
from src.config import Settings, get_settings
from src.shared.redis_keys import redis_keys


def get_jwt_strategy(settings=Depends(get_settings)) -> JWTStrategy:
    return JWTStrategy(
        secret=settings.auth.jwt_secret,
        algorithm=settings.auth.jwt_algorithm,
        lifetime_seconds=settings.auth.jwt_lifetime_seconds,
    )


class RefreshTokenManager:
    """
    Refresh token manager that handles creation, verification, and revocation of refresh tokens.

    Special Notes: 1. `fastapi-users` does not provide built-in support for refresh tokens.
    2. Revocation (token blacklist) is implemented via cache-based approach, which requires refresh token stateful (opaque token).
    3. JWT (access token) remains stateless.
    """

    def __init__(self, cache: CacheProtocol, settings: Settings):
        self._cache = cache
        self.settings = settings

    async def create_refresh_token(
        self, user_id: int, device_info: str | None = None
    ) -> str:
        """Create a refresh token for the given user.

        Args:
            user_id: The user's ID.
            device_info: Optional device information for tracking. Retrieved from User-Agent Header.

        Returns:
            The generated refresh token string.
        """
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        value = f"{user_id}:{device_info or 'unknown'}:{datetime.now(timezone.utc).isoformat()}"

        await self._cache.set(
            redis_keys.refresh_token(token_hash=token_hash),
            value,
            ttl=self.settings.auth.refresh_token_lifetime_seconds,
        )
        return token

    async def verify_refresh_token(self, token: str) -> int | None:
        """Verify the given refresh token.

        Returns:
            The user ID if the token is valid, None otherwise.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        value = await self._cache.get(redis_keys.refresh_token(token_hash=token_hash))
        if not value:
            return None

        parts = value.split(":", maxsplit=2)
        user_id = int(parts[0])
        token_created_time = parts[2]

        revoke_time = await self._cache.get(redis_keys.user_revoked(user_id=user_id))
        if revoke_time and token_created_time < revoke_time:
            return None

        return user_id

    async def revoke_token(self, token: str) -> None:
        """Revoke a specific refresh token, deleting it from the cache."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        await self._cache.delete(redis_keys.refresh_token(token_hash=token_hash))

    async def revoke_all_user_tokens(self, user_id: int) -> None:
        """Add the user to the revoked list to invalidate all their refresh tokens."""
        revoke_time = datetime.now(timezone.utc).isoformat()
        await self._cache.set(
            redis_keys.user_revoked(user_id=user_id),
            revoke_time,
            ttl=self.settings.auth.refresh_token_lifetime_seconds,
        )


def get_refresh_token_manager(
    cache: CacheProtocol = Depends(get_cache),
    settings: Settings = Depends(get_settings),
) -> RefreshTokenManager:
    return RefreshTokenManager(cache, settings)


bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
