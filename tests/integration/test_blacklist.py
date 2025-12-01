"""黑名单机制集成测试

测试 Token 黑名单的完整流程。
"""

import pytest
from datetime import datetime, timezone

from src.auth.cache_token_store import CacheTokenStore


class MockCache:
    """模拟缓存实现"""

    def __init__(self):
        self._data = {}
        self._ttl = {}

    async def set(self, key, value, ttl=None):
        self._data[key] = value
        if ttl:
            self._ttl[key] = ttl

    async def get(self, key):
        return self._data.get(key)

    async def delete(self, key):
        if key in self._data:
            del self._data[key]
        if key in self._ttl:
            del self._ttl[key]


class TestBlacklistIntegration:
    """黑名单机制集成测试套件"""

    @pytest.fixture
    def cache_store(self):
        """创建缓存存储实例"""
        store = CacheTokenStore()
        store.set_cache(MockCache())
        return store

    @pytest.mark.asyncio
    async def test_access_token_blacklist(self, cache_store):
        """测试 access_token 黑名单机制"""
        token_id = "access-token-123"
        user_id = 456

        # 验证初始状态不在黑名单
        assert not await cache_store.is_access_token_blacklisted(token_id)

        # 加入黑名单
        await cache_store.blacklist_access_token(token_id, user_id)

        # 验证在黑名单中
        assert await cache_store.is_access_token_blacklisted(token_id)

    @pytest.mark.asyncio
    async def test_multiple_access_tokens_blacklist(self, cache_store):
        """测试多个 access_token 黑名单"""
        tokens = [
            ("token-1", 101),
            ("token-2", 102),
            ("token-3", 103),
        ]

        # 加入所有 token 到黑名单
        for token_id, user_id in tokens:
            await cache_store.blacklist_access_token(token_id, user_id)

        # 验证所有 token 都在黑名单中
        for token_id, _ in tokens:
            assert await cache_store.is_access_token_blacklisted(token_id)

    @pytest.mark.asyncio
    async def test_blacklist_with_ttl(self, cache_store):
        """测试带 TTL 的黑名单"""
        token_id = "ttl-token-456"
        user_id = 789
        ttl_seconds = 10  # 10 秒 TTL

        # 加入黑名单（带 TTL）
        await cache_store.blacklist_access_token(
            token_id, user_id, ttl=ttl_seconds
        )

        # 验证在黑名单中
        assert await cache_store.is_access_token_blacklisted(token_id)

        # 注意：这里没有实际测试 TTL 过期，
        # 因为需要等待或模拟时间流逝

    @pytest.mark.asyncio
    async def test_user_tokens_tracking(self, cache_store):
        """测试用户 token 追踪"""
        user_id = 999

        # 存储用户 token
        token_id_1 = "refresh-token-1"
        expires_at = int(datetime.now(timezone.utc).timestamp()) + 3600

        await cache_store.store_refresh_token(token_id_1, user_id, expires_at)

        # 验证用户活跃 token
        active_token = await cache_store.get_user_active_refresh_token(user_id)
        assert active_token == token_id_1

        # 新登录（替换 token）
        token_id_2 = "refresh-token-2"
        await cache_store.store_refresh_token(token_id_2, user_id, expires_at)

        # 验证用户活跃 token 已更新
        active_token = await cache_store.get_user_active_refresh_token(user_id)
        assert active_token == token_id_2

        # 验证旧的 token 仍然存在（但业务逻辑上不再使用）
        # 在单设备登录场景中，旧的 access_token 会被撤销，
        # 但 refresh_token 仍可用于刷新

    @pytest.mark.asyncio
    async def test_revoke_all_user_tokens(self, cache_store):
        """测试撤销用户所有 token（单设备登录）"""
        user_id = 123

        # 存储多个 token（模拟多次登录）
        token_ids = ["token-1", "token-2", "token-3"]
        expires_at = int(datetime.now(timezone.utc).timestamp()) + 3600

        for token_id in token_ids:
            await cache_store.store_refresh_token(token_id, user_id, expires_at)

        # 在单设备登录中，只有最新的 token（token-3）是有效的
        # 验证当前活跃 token
        active_token = await cache_store.get_user_active_refresh_token(user_id)
        assert active_token == "token-3"

        # 撤销所有 token（只删除当前活跃的）
        await cache_store.revoke_all_user_tokens(user_id)

        # 验证用户活跃 token 已被删除
        assert (
            await cache_store.get_user_active_refresh_token(user_id) is None
        )

        # 注意：在单设备登录场景中，旧的 refresh_token 不会立即被删除
        # 它们会自然过期，因为只有最新的 token 才会被用于刷新操作
        # 这个测试验证的是当前活跃 token 被正确删除

    @pytest.mark.asyncio
    async def test_blacklist_persistence(self, cache_store):
        """测试黑名单持久化（Redis 重启后数据会丢失，但这是可接受的）"""
        token_id = "persistent-token-789"
        user_id = 555

        # 加入黑名单
        await cache_store.blacklist_access_token(token_id, user_id)

        # 验证在黑名单中
        assert await cache_store.is_access_token_blacklisted(token_id)

        # 注意：在实际 Redis 环境中，重启会导致数据丢失，
        # 但 access_token 会因为 TTL 自动过期，所以这是可接受的
