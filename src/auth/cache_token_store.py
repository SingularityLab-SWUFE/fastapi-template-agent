"""Redis 缓存存储管理

负责在 Redis 中存储 refresh_token 和 access_token 黑名单。
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
import json


class CacheTokenStore:
    """基于缓存的 Token 存储"""

    def __init__(self) -> None:
        """初始化缓存存储"""
        # 这里通过依赖注入获取缓存实例
        # 在实际使用时通过 get_cache() 获取
        self._cache = None

    def set_cache(self, cache) -> None:
        """设置缓存实例

        Args:
            cache: 缓存实例（支持 Redis 或本地缓存）
        """
        self._cache = cache

    def _ensure_cache(self) -> None:
        """确保缓存实例已设置"""
        if self._cache is None:
            raise RuntimeError("缓存实例未设置，请先调用 set_cache()")

    async def store_refresh_token(
        self, token_id: str, user_id: int, expires_at: int
    ) -> None:
        """存储 refresh_token

        Args:
            token_id: refresh_token ID
            user_id: 用户 ID
            expires_at: 过期时间戳
        """
        self._ensure_cache()

        key = f"refresh_token:{token_id}"
        value = {
            "user_id": user_id,
            "expires_at": expires_at,
            "created_at": int(datetime.now(timezone.utc).timestamp()),
        }

        # 计算 TTL（秒）
        ttl = max(0, expires_at - int(datetime.now(timezone.utc).timestamp()))

        await self._cache.set(key, json.dumps(value), ttl=ttl)

        # 存储用户当前活跃的 refresh_token（单设备登录）
        user_token_key = f"user_tokens:{user_id}:refresh"
        await self._cache.set(user_token_key, token_id, ttl=ttl)

    async def get_refresh_token_user_id(self, token_id: str) -> Optional[int]:
        """获取 refresh_token 对应的用户 ID

        Args:
            token_id: refresh_token ID

        Returns:
            用户 ID，如果 token 无效则返回 None
        """
        self._ensure_cache()

        key = f"refresh_token:{token_id}"
        value = await self._cache.get(key)

        if not value:
            return None

        try:
            data = json.loads(value)
            expires_at = data.get("expires_at")
            user_id = data.get("user_id")

            # 检查是否过期
            if expires_at and int(datetime.now(timezone.utc).timestamp()) > expires_at:
                await self.delete_refresh_token(token_id)
                return None

            return user_id
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    async def delete_refresh_token(self, token_id: str) -> bool:
        """删除 refresh_token

        Args:
            token_id: refresh_token ID

        Returns:
            删除是否成功
        """
        self._ensure_cache()

        key = f"refresh_token:{token_id}"

        # 先获取用户 ID，用于清理用户 token 追踪
        user_id = await self.get_refresh_token_user_id(token_id)

        # 删除 refresh_token
        await self._cache.delete(key)

        # 如果有用户 ID，清理用户 token 追踪
        if user_id:
            user_token_key = f"user_tokens:{user_id}:refresh"
            current_token = await self._cache.get(user_token_key)
            if current_token == token_id:
                await self._cache.delete(user_token_key)

        return True

    async def blacklist_access_token(
        self, token_id: str, user_id: int, ttl: Optional[int] = None
    ) -> None:
        """将 access_token 加入黑名单

        Args:
            token_id: access_token ID
            user_id: 用户 ID
            ttl: 黑名单有效期（秒），默认为 access_token 的剩余时间
        """
        self._ensure_cache()

        key = f"blacklist:access:{token_id}"
        value = {
            "user_id": user_id,
            "revoked_at": int(datetime.now(timezone.utc).timestamp()),
        }

        # 如果未指定 TTL，默认为 30 天
        if ttl is None:
            ttl = 30 * 24 * 60 * 60

        await self._cache.set(key, json.dumps(value), ttl=ttl)

    async def is_access_token_blacklisted(self, token_id: str) -> bool:
        """检查 access_token 是否在黑名单中

        Args:
            token_id: access_token ID

        Returns:
            token 是否在黑名单中
        """
        self._ensure_cache()

        key = f"blacklist:access:{token_id}"
        value = await self._cache.get(key)

        return value is not None

    async def get_user_active_refresh_token(self, user_id: int) -> Optional[str]:
        """获取用户当前活跃的 refresh_token

        Args:
            user_id: 用户 ID

        Returns:
            活跃的 refresh_token ID，如果没有则返回 None
        """
        self._ensure_cache()

        key = f"user_tokens:{user_id}:refresh"
        token_id = await self._cache.get(key)

        return token_id if token_id else None

    async def revoke_all_user_tokens(self, user_id: int) -> None:
        """撤销用户的所有 token

        Args:
            user_id: 用户 ID
        """
        self._ensure_cache()

        # 删除用户当前的 refresh_token
        user_token_key = f"user_tokens:{user_id}:refresh"
        current_token = await self._cache.get(user_token_key)

        if current_token:
            await self.delete_refresh_token(current_token)

        # 注意：这里只删除了用户当前的 refresh_token（单设备登录）
        # 旧的 refresh_token 会自动过期，它们仍然存在于缓存中但不会被使用
        # 这是单设备登录的设计：只有最新的 token 是有效的

        # 注意：access_token 黑名单会自动过期
        # 如果需要立即清理所有 access_token 黑名单，可以遍历所有 blacklist:access:* 键
        # 但这在生产环境中可能会影响性能
