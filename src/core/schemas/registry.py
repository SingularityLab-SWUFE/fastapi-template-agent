from typing import Protocol


class RedisKey(Protocol):
    """Protocol for Redis key generators."""

    def __call__(self, **kwargs: str | int) -> str: ...


class _RefreshToken:
    """Refresh token key: refresh_token:{token_hash}"""

    namespace = "refresh_token"

    def __call__(self, token_hash: str) -> str:
        return f"{self.namespace}:{token_hash}"


class _UserRevoked:
    """User revoked key: user_revoked:{user_id}"""

    namespace = "user_revoked"

    def __call__(self, user_id: int) -> str:
        return f"{self.namespace}:{user_id}"


class RedisKeyRegistry:
    """Registry for all Redis keys used in the application."""

    refresh_token = _RefreshToken()
    user_revoked = _UserRevoked()


redis_keys = RedisKeyRegistry()
