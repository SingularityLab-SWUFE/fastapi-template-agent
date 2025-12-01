"""Token 管理器单元测试"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from src.auth.token_manager import TokenManager


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


class TestTokenManager:
    """Token 管理器测试套件"""

    @pytest.fixture
    def token_manager(self):
        """创建 Token 管理器实例"""
        manager = TokenManager(
            secret_key="test-secret-key",
            algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7,
        )

        # 设置模拟缓存
        mock_cache = MockCache()
        manager.cache_store.set_cache(mock_cache)

        return manager

    def test_create_access_token(self, token_manager):
        """测试创建 access_token"""
        user_id = 123
        username = "testuser"

        access_token = token_manager.create_access_token(user_id, username)

        assert isinstance(access_token, str)
        assert len(access_token) > 0

    @pytest.mark.asyncio
    async def test_create_refresh_token(self, token_manager):
        """测试创建 refresh_token"""
        user_id = 123

        refresh_token = await token_manager.create_refresh_token(user_id)

        assert isinstance(refresh_token, str)
        assert len(refresh_token) > 0

    @pytest.mark.asyncio
    async def test_create_token_pair(self, token_manager):
        """测试创建 token 对"""
        user_id = 123
        username = "testuser"

        tokens = await token_manager.create_token_pair(user_id, username)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"] == "bearer"

    def test_password_hash_and_verify(self, token_manager):
        """测试密码哈希和验证"""
        password = "test-password-123"
        hashed = TokenManager.get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0

        # 验证正确密码
        assert TokenManager.verify_password(password, hashed)

        # 验证错误密码
        assert not TokenManager.verify_password("wrong-password", hashed)

    @pytest.mark.asyncio
    async def test_verify_access_token_success(self, token_manager):
        """测试验证有效的 access_token"""
        user_id = 123
        username = "testuser"

        access_token = token_manager.create_access_token(user_id, username)

        payload = await token_manager.verify_access_token(access_token)

        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["username"] == username
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    @pytest.mark.asyncio
    async def test_verify_access_token_invalid(self, token_manager):
        """测试验证无效的 access_token"""
        # 无效的 token
        payload = await token_manager.verify_access_token("invalid-token")

        assert payload is None

        # 过期或篡改的 token
        tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
        payload = await token_manager.verify_access_token(tampered_token)

        assert payload is None

    def test_verify_password(self, token_manager):
        """测试密码验证"""
        plain_password = "test123"
        hashed_password = TokenManager.get_password_hash(plain_password)

        assert token_manager.verify_password(plain_password, hashed_password)
        assert not token_manager.verify_password("wrong", hashed_password)
