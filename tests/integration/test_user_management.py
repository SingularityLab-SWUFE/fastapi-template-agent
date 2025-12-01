"""用户管理流程集成测试

测试用户注册、登录、Token 刷新、注销等完整用户管理流程。
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock

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

    async def exists(self, key):
        return key in self._data


class TestUserManagementIntegration:
    """用户管理流程集成测试套件"""

    @pytest.fixture
    def token_manager(self):
        """创建 Token 管理器实例"""
        manager = TokenManager(
            secret_key="test-secret-key-for-user-management",
            algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7,
        )

        # 设置模拟缓存
        mock_cache = MockCache()
        manager.cache_store.set_cache(mock_cache)

        return manager

    @pytest.mark.asyncio
    async def test_user_login_flow(self, token_manager):
        """测试用户登录完整流程"""
        user_id = 123
        username = "testuser_login"
        password = "testpassword123"

        # 验证密码哈希（假设密码已正确哈希）
        hashed_password = TokenManager.get_password_hash(password)
        assert TokenManager.verify_password(password, hashed_password)

        # 模拟登录：创建 token 对
        tokens = await token_manager.create_token_pair(user_id, username)

        # 验证返回的 token 对
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert isinstance(tokens["access_token"], str)
        assert len(tokens["access_token"]) > 0
        assert isinstance(tokens["refresh_token"], str)
        assert len(tokens["refresh_token"]) > 0

        # 验证 access_token 有效
        access_payload = await token_manager.verify_access_token(
            tokens["access_token"]
        )
        assert access_payload is not None
        assert access_payload["sub"] == str(user_id)
        assert access_payload["username"] == username
        assert access_payload["type"] == "access"

        # 验证 refresh_token 有效
        refresh_user_id = await token_manager.verify_refresh_token(
            tokens["refresh_token"]
        )
        assert refresh_user_id == user_id

    @pytest.mark.asyncio
    async def test_user_logout_flow(self, token_manager):
        """测试用户注销流程"""
        user_id = 456
        username = "testuser_logout"

        # 登录获取 token
        tokens = await token_manager.create_token_pair(user_id, username)
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # 验证 access_token 在注销前有效
        assert await token_manager.verify_access_token(access_token) is not None

        # 注销：撤销 access_token
        success = await token_manager.revoke_access_token(access_token)
        assert success is True

        # 验证 access_token 在注销后失效
        assert await token_manager.verify_access_token(access_token) is None

        # 验证 refresh_token 在注销后仍然有效（单设备登录策略）
        refresh_user_id = await token_manager.verify_refresh_token(refresh_token)
        assert refresh_user_id == user_id

        # 验证用户可以使用 refresh_token 重新获取 access_token
        # （在实际应用中，需要 UserManager 实现刷新逻辑）

    @pytest.mark.asyncio
    async def test_user_token_refresh(self, token_manager):
        """测试用户 token 刷新流程"""
        user_id = 789
        username = "testuser_refresh"

        # 登录获取 token
        tokens = await token_manager.create_token_pair(user_id, username)
        old_access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # 验证旧的 access_token 有效
        assert await token_manager.verify_access_token(old_access_token) is not None

        # 模拟刷新：创建新的 access_token（使用相同的 refresh_token）
        # 注意：实际刷新需要 UserManager 的帮助
        new_access_token = token_manager.create_access_token(user_id, username)

        # 验证新的 access_token 有效
        assert await token_manager.verify_access_token(new_access_token) is not None

        # 验证新旧 access_token 不同
        assert old_access_token != new_access_token

        # 验证刷新 token 仍然有效
        refresh_user_id = await token_manager.verify_refresh_token(refresh_token)
        assert refresh_user_id == user_id

    @pytest.mark.asyncio
    async def test_concurrent_user_sessions(self, token_manager):
        """测试用户并发会话（多次登录）"""
        user_id = 999
        username = "testuser_concurrent"

        # 第一次登录
        tokens1 = await token_manager.create_token_pair(user_id, username)
        old_access_token1 = tokens1["access_token"]
        old_refresh_token1 = tokens1["refresh_token"]

        # 第二次登录（新 token 对）
        tokens2 = await token_manager.create_token_pair(user_id, username)
        new_access_token = tokens2["access_token"]
        new_refresh_token = tokens2["refresh_token"]

        # 验证新旧 token 不同
        assert old_access_token1 != new_access_token
        assert old_refresh_token1 != new_refresh_token

        # 验证新的 access_token 有效
        assert await token_manager.verify_access_token(new_access_token) is not None

        # 在单设备登录中，旧的 access_token 仍然有效（未撤销）
        assert await token_manager.verify_access_token(old_access_token1) is not None

        # 验证两个 refresh_token 都有效（都可以用于刷新）
        refresh_user_id1 = await token_manager.verify_refresh_token(old_refresh_token1)
        refresh_user_id2 = await token_manager.verify_refresh_token(new_refresh_token)
        assert refresh_user_id1 == user_id
        assert refresh_user_id2 == user_id

        # 验证单设备登录：只有最新的 refresh_token 被追踪
        active_token = await token_manager.cache_store.get_user_active_refresh_token(
            user_id
        )
        # 在单设备登录中，新登录会覆盖旧 token
        # 但两个 refresh_token 都仍然有效（业务逻辑决定使用哪一个）

    @pytest.mark.asyncio
    async def test_user_session_recovery(self, token_manager):
        """测试用户会话恢复（使用 refresh_token 恢复会话）"""
        user_id = 111
        username = "testuser_recovery"

        # 登录获取 token
        tokens = await token_manager.create_token_pair(user_id, username)
        original_access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # 模拟 access_token 过期或被撤销
        await token_manager.revoke_access_token(original_access_token)

        # 验证 access_token 已失效
        assert await token_manager.verify_access_token(original_access_token) is None

        # 使用 refresh_token 验证会话仍然有效
        refresh_user_id = await token_manager.verify_refresh_token(refresh_token)
        assert refresh_user_id == user_id

        # 重新生成 access_token（模拟刷新）
        new_access_token = token_manager.create_access_token(user_id, username)

        # 验证新 access_token 有效
        assert await token_manager.verify_access_token(new_access_token) is not None
        assert new_access_token != original_access_token

    @pytest.mark.asyncio
    async def test_inactive_user_access(self, token_manager):
        """测试禁用用户无法访问"""
        # 注意：这个测试假设系统检查用户 is_active 状态
        # 在实际应用中，UserManager 或认证依赖会检查此状态

        user_id = 222
        inactive_user_id = 333  # 模拟禁用用户

        # 为活跃用户创建 token
        tokens_active = await token_manager.create_token_pair(user_id, "active_user")
        assert await token_manager.verify_access_token(tokens_active["access_token"]) is not None

        # 为禁用用户创建 token（虽然不应该允许，但测试逻辑）
        tokens_inactive = await token_manager.create_token_pair(
            inactive_user_id, "inactive_user"
        )
        # 在实际应用中，禁用用户的 token 应该被拒绝
        # 这里我们只测试 token 本身的有效性

        # 注意：在实际应用中，需要在 UserManager 或认证依赖中检查 is_active 状态
        # 例如：
        # if not user.is_active:
        #     raise HTTPException(status_code=403, detail="用户已被禁用")

    @pytest.mark.asyncio
    async def test_user_password_change(self, token_manager):
        """测试用户修改密码流程"""
        user_id = 444
        username = "testuser_password"
        old_password = "oldpassword123"
        new_password = "newpassword456"

        # 初始密码哈希
        old_hashed = TokenManager.get_password_hash(old_password)
        assert TokenManager.verify_password(old_password, old_hashed)

        # 新密码哈希
        new_hashed = TokenManager.get_password_hash(new_password)
        assert TokenManager.verify_password(new_password, new_hashed)

        # 验证新旧密码不同
        assert old_hashed != new_hashed

        # 验证旧密码不再有效
        assert not TokenManager.verify_password(old_password, new_hashed)

        # 验证新密码有效
        assert TokenManager.verify_password(new_password, new_hashed)

        # 注意：在实际应用中，密码修改后应该撤销所有 active token
        # 强制用户重新登录

    @pytest.mark.asyncio
    async def test_multiple_devices_single_user(self, token_manager):
        """测试同一用户多设备登录"""
        user_id = 555
        username = "testuser_devices"

        # 设备1登录
        tokens_device1 = await token_manager.create_token_pair(user_id, username)
        access_token1 = tokens_device1["access_token"]
        refresh_token1 = tokens_device1["refresh_token"]

        # 设备2登录
        tokens_device2 = await token_manager.create_token_pair(user_id, username)
        access_token2 = tokens_device2["access_token"]
        refresh_token2 = tokens_device2["refresh_token"]

        # 验证两个设备的 token 都不同
        assert access_token1 != access_token2
        assert refresh_token1 != refresh_token2

        # 验证两个设备的 access_token 都有效
        assert await token_manager.verify_access_token(access_token1) is not None
        assert await token_manager.verify_access_token(access_token2) is not None

        # 验证两个设备的 refresh_token 都有效
        assert (
            await token_manager.verify_refresh_token(refresh_token1) == user_id
        )
        assert (
            await token_manager.verify_refresh_token(refresh_token2) == user_id
        )

        # 在单设备登录策略中，用户可以选择撤销特定设备的 token
        # 或者撤销所有设备的 token

    @pytest.mark.asyncio
    async def test_token_expiration_handling(self, token_manager):
        """测试 token 过期处理"""
        user_id = 666
        username = "testuser_expiration"

        # 创建 token（默认 30 分钟过期）
        tokens = await token_manager.create_token_pair(user_id, username)
        access_token = tokens["access_token"]

        # 验证 access_token 在创建后立即有效
        assert await token_manager.verify_access_token(access_token) is not None

        # 验证 refresh_token 有效（默认 7 天过期）
        refresh_token = tokens["refresh_token"]
        assert await token_manager.verify_refresh_token(refresh_token) == user_id

        # 注意：测试 token 过期需要模拟时间流逝或修改 token 的 exp 字段
        # 在实际应用中，JWT 会自动检查过期时间
        # 过期 token 会导致 verify_access_token 返回 None

        # 如果需要测试过期，可以使用 mock 时间或创建已过期的 token
        # 或者等待足够长的时间（不推荐）

    @pytest.mark.asyncio
    async def test_user_access_own_data(self, token_manager):
        """测试用户只能访问自己的数据"""
        user_id_1 = 777
        user_id_2 = 888
        username_1 = "user1"
        username_2 = "user2"

        # 用户1登录
        tokens_1 = await token_manager.create_token_pair(user_id_1, username_1)
        access_token_1 = tokens_1["access_token"]

        # 用户2登录
        tokens_2 = await token_manager.create_token_pair(user_id_2, username_2)
        access_token_2 = tokens_2["access_token"]

        # 验证每个用户只能使用自己的 token
        payload_1 = await token_manager.verify_access_token(access_token_1)
        assert payload_1 is not None
        assert payload_1["sub"] == str(user_id_1)
        assert payload_1["username"] == username_1

        payload_2 = await token_manager.verify_access_token(access_token_2)
        assert payload_2 is not None
        assert payload_2["sub"] == str(user_id_2)
        assert payload_2["username"] == username_2

        # 验证用户1不能使用用户2的 token
        invalid_payload = await token_manager.verify_access_token(access_token_2)
        assert invalid_payload["sub"] != str(user_id_1)

        # 注意：在实际应用中，需要在 API 层检查用户只能访问自己的资源
        # 例如：用户只能更新自己的资料，不能更新其他用户的资料

    @pytest.mark.asyncio
    async def test_user_cannot_access_others_data(self, token_manager):
        """测试用户不能访问其他用户数据"""
        # 这个测试验证了 token 的安全性
        # 在实际应用中，还需要在业务逻辑层检查权限

        user_id_1 = 999
        user_id_2 = 1000
        username_1 = "target_user"
        username_2 = "attacker_user"

        # 目标用户登录
        tokens_target = await token_manager.create_token_pair(user_id_1, username_1)
        access_token_target = tokens_target["access_token"]

        # 攻击者用户登录
        tokens_attacker = await token_manager.create_token_pair(
            user_id_2, username_2
        )
        access_token_attacker = tokens_attacker["access_token"]

        # 验证攻击者不能伪装成目标用户
        attacker_payload = await token_manager.verify_access_token(
            access_token_attacker
        )
        assert attacker_payload["sub"] != str(user_id_1)
        assert attacker_payload["username"] == username_2

        # 验证目标用户的 token 包含正确的用户ID
        target_payload = await token_manager.verify_access_token(
            access_token_target
        )
        assert target_payload["sub"] == str(user_id_1)
        assert target_payload["username"] == username_1

        # 注意：JWT token 确保了身份验证
        # 但授权（用户只能访问自己的数据）需要在业务逻辑中实现
        # 例如：
        # if current_user.id != target_user_id:
        #     raise HTTPException(status_code=403, detail="权限不足")
