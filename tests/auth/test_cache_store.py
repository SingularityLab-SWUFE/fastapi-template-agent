"""缓存存储单元测试"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
import json

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

    async def exists(self, key):
        return key in self._data


class TestCacheTokenStore:
    """缓存存储测试套件"""

    @pytest.fixture
    def cache_store(self):
        """创建缓存存储实例"""
        store = CacheTokenStore()
        store.set_cache(MockCache())
        return store

    @pytest.mark.asyncio
    async def test_store_refresh_token(self, cache_store):
        """测试存储 refresh_token"""
        token_id = "test-token-id"
        user_id = 123
        expires_at = int(datetime.now(timezone.utc).timestamp()) + 3600

        await cache_store.store_refresh_token(token_id, user_id, expires_at)

        # 验证存储成功
        retrieved_user_id = await cache_store.get_refresh_token_user_id(token_id)
        assert retrieved_user_id == user_id

    @pytest.mark.asyncio
    async def test_get_refresh_token_user_id(self, cache_store):
        """测试获取 refresh_token 对应的用户 ID"""
        token_id = "test-token-id"
        user_id = 456
        expires_at = int(datetime.now(timezone.utc).timestamp()) + 3600

        # 先存储
        await cache_store.store_refresh_token(token_id, user_id, expires_at)

        # 再获取
        retrieved_user_id = await cache_store.get_refresh_token_user_id(token_id)

        assert retrieved_user_id == user_id

    @pytest.mark.asyncio
    async def test_get_refresh_token_invalid(self, cache_store):
        """测试获取无效的 refresh_token"""
        invalid_token_id = "invalid-token"

        user_id = await cache_store.get_refresh_token_user_id(invalid_token_id)

        assert user_id is None

    @pytest.mark.asyncio
    async def test_delete_refresh_token(self, cache_store):
        """测试删除 refresh_token"""
        token_id = "test-token-id"
        user_id = 789
        expires_at = int(datetime.now(timezone.utc).timestamp()) + 3600

        # 存储
        await cache_store.store_refresh_token(token_id, user_id, expires_at)

        # 验证存在
        assert await cache_store.get_refresh_token_user_id(token_id) == user_id

        # 删除
        await cache_store.delete_refresh_token(token_id)

        # 验证已删除
        assert await cache_store.get_refresh_token_user_id(token_id) is None

    @pytest.mark.asyncio
    async def test_blacklist_access_token(self, cache_store):
        """测试将 access_token 加入黑名单"""
        token_id = "access-token-id"
        user_id = 999

        await cache_store.blacklist_access_token(token_id, user_id)

        # 验证在黑名单中
        is_blacklisted = await cache_store.is_access_token_blacklisted(token_id)
        assert is_blacklisted

    @pytest.mark.asyncio
    async def test_is_access_token_blacklisted(self, cache_store):
        """测试检查 access_token 是否在黑名单中"""
        token_id = "access-token-id"

        # 未加入黑名单
        is_blacklisted = await cache_store.is_access_token_blacklisted(token_id)
        assert not is_blacklisted

        # 加入黑名单后
        await cache_store.blacklist_access_token(token_id, 123)
        is_blacklisted = await cache_store.is_access_token_blacklisted(token_id)
        assert is_blacklisted

    @pytest.mark.asyncio
    async def test_revoke_all_user_tokens(self, cache_store):
        """测试撤销用户所有 token（单设备登录）"""
        user_id = 123
        token_id_1 = "token-1"
        token_id_2 = "token-2"
        expires_at = int(datetime.now(timezone.utc).timestamp()) + 3600

        # 存储两个 token（模拟两次登录，第二次会覆盖第一次）
        await cache_store.store_refresh_token(token_id_1, user_id, expires_at)
        await cache_store.store_refresh_token(token_id_2, user_id, expires_at)

        # 在单设备登录中，只有最新的 token（token_id_2）是有效的
        # 旧的 token（token_id_1）仍然存在于缓存中，但不会被使用

        # 验证当前活跃的 token 是 token_id_2
        active_token = await cache_store.get_user_active_refresh_token(user_id)
        assert active_token == token_id_2

        # 撤销所有 token
        await cache_store.revoke_all_user_tokens(user_id)

        # 验证当前活跃的 token 已被删除
        assert await cache_store.get_user_active_refresh_token(user_id) is None

        # 注意：在单设备登录场景中，旧的 refresh_token 不会立即被删除
        # 它们会自然过期，因为只有最新的 token 才会被用于刷新操作
        # 这个测试验证的是当前活跃 token 被正确删除
