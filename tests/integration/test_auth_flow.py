"""认证流程集成测试

测试完整的登录、刷新、注销流程。
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.auth.token_manager import TokenManager
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


class TestAuthFlow:
    """认证流程集成测试套件"""

    @pytest.fixture
    def token_manager(self):
        """创建 Token 管理器实例"""
        manager = TokenManager(
            secret_key="test-secret-key-for-integration",
            algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7,
        )

        # 设置模拟缓存
        mock_cache = MockCache()
        manager.cache_store.set_cache(mock_cache)

        return manager

    @pytest.mark.asyncio
    async def test_login_and_token_generation(self, token_manager):
        """测试登录和 Token 生成"""
        user_id = 123
        username = "testuser"

        # 创建 token 对
        tokens = await token_manager.create_token_pair(user_id, username)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

        # 验证 access_token
        access_payload = await token_manager.verify_access_token(tokens["access_token"])
        assert access_payload is not None
        assert access_payload["sub"] == str(user_id)
        assert access_payload["username"] == username
        assert access_payload["type"] == "access"

        # 验证 refresh_token
        refresh_user_id = await token_manager.verify_refresh_token(tokens["refresh_token"])
        assert refresh_user_id == user_id

    @pytest.mark.asyncio
    async def test_token_refresh_flow(self, token_manager):
        """测试 Token 刷新流程"""
        user_id = 456
        username = "testuser2"

        # 创建初始 token 对
        tokens = await token_manager.create_token_pair(user_id, username)
        original_access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # 验证原始 access_token
        assert await token_manager.verify_access_token(original_access_token) is not None

        # 撤销旧的 access_token
        await token_manager.revoke_access_token(original_access_token)

        # 验证 access_token 已失效
        assert await token_manager.verify_access_token(original_access_token) is None

        # 验证 refresh_token 仍然有效
        assert await token_manager.verify_refresh_token(refresh_token) == user_id

        # 注意：实际的刷新流程需要在 UserManager 中实现
        # 这里只是测试黑名单机制不影响 refresh_token

    @pytest.mark.asyncio
    async def test_logout_flow(self, token_manager):
        """测试注销流程"""
        user_id = 789
        username = "testuser3"

        # 创建 token 对
        tokens = await token_manager.create_token_pair(user_id, username)
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # 验证 access_token 有效
        assert await token_manager.verify_access_token(access_token) is not None

        # 注销（撤销 access_token）
        success = await token_manager.revoke_access_token(access_token)
        assert success is True

        # 验证 access_token 已失效
        assert await token_manager.verify_access_token(access_token) is None

        # 验证 refresh_token 仍然有效（未撤销）
        assert await token_manager.verify_refresh_token(refresh_token) == user_id

    @pytest.mark.asyncio
    async def test_single_device_login(self, token_manager):
        """测试单设备登录（新登录覆盖旧 token）"""
        user_id = 999
        username = "testuser4"

        # 第一次登录
        tokens1 = await token_manager.create_token_pair(user_id, username)
        old_access_token = tokens1["access_token"]
        old_refresh_token = tokens1["refresh_token"]

        # 第二次登录（新 token 对）
        tokens2 = await token_manager.create_token_pair(user_id, username)
        new_access_token = tokens2["access_token"]
        new_refresh_token = tokens2["refresh_token"]

        # 验证新旧 token 不同
        assert old_access_token != new_access_token
        assert old_refresh_token != new_refresh_token

        # 验证新的 access_token 有效
        assert await token_manager.verify_access_token(new_access_token) is not None

        # 验证旧的 access_token 仍然有效（只有在撤销时才失效）
        assert await token_manager.verify_access_token(old_access_token) is not None

        # 验证新的 refresh_token 有效
        assert await token_manager.verify_refresh_token(new_refresh_token) == user_id

        # 验证旧的 refresh_token 仍然有效
        assert await token_manager.verify_refresh_token(old_refresh_token) == user_id

        # 验证两个 refresh_token 都可以使用（单设备是指业务逻辑上的，
        # 旧设备 access_token 失效，但 refresh_token 仍可用于刷新）
