"""认证中间件测试

测试全局认证中间件的功能。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import RequestResponseEndpoint

from src.core.middleware.auth_middleware import AuthMiddleware
from src.auth.token_manager import TokenManager
from src.auth.dependencies import set_token_manager, _get_token_manager


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


class TestAuthMiddleware:
    """认证中间件测试套件"""

    @pytest.fixture
    def app(self):
        """创建测试 FastAPI 应用"""
        app = FastAPI()

        @app.get("/protected")
        async def protected_endpoint(request: Request):
            # 检查中间件是否设置了 user_info
            if hasattr(request.state, "user_info"):
                return {
                    "status": "authenticated",
                    "user_id": request.state.user_info["id"],
                    "username": request.state.user_info["username"],
                }
            else:
                return {"status": "anonymous"}

        @app.get("/public")
        async def public_endpoint():
            return {"status": "public"}

        return app

    @pytest.fixture
    def token_manager(self):
        """创建 Token 管理器实例"""
        manager = TokenManager(
            secret_key="test-secret-key-for-middleware",
            algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7,
            issuer="test-issuer",
            audience="test-audience",
        )

        # 设置模拟缓存
        mock_cache = MockCache()
        manager.cache_store.set_cache(mock_cache)

        return manager

    @pytest.mark.asyncio
    async def test_middleware_skips_public_paths(self, app):
        """测试中间件跳过公共路径"""
        # 注册中间件
        app.add_middleware(AuthMiddleware)

        # 使用 TestClient 测试
        with TestClient(app) as client:
            response = client.get("/public")
            assert response.status_code == 200
            assert response.json()["status"] == "public"

    @pytest.mark.asyncio
    async def test_middleware_without_token(self, app, token_manager):
        """测试中间件在没有 token 的情况下处理请求"""
        # 设置 Token 管理器
        set_token_manager(token_manager)

        # 注册中间件
        app.add_middleware(AuthMiddleware)

        # 使用 TestClient 测试
        with TestClient(app) as client:
            response = client.get("/protected")
            assert response.status_code == 200
            # 应该返回匿名状态，因为没有认证
            assert response.json()["status"] == "anonymous"

    @pytest.mark.asyncio
    async def test_middleware_with_valid_token(self, app, token_manager):
        """测试中间件使用有效 token 处理请求"""
        # 设置 Token 管理器
        set_token_manager(token_manager)

        # 创建用户 token
        user_id = 123
        username = "testuser"
        access_token = token_manager.create_access_token(user_id, username)

        # 注册中间件
        app.add_middleware(AuthMiddleware)

        # 使用 TestClient 测试
        with TestClient(app) as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = client.get("/protected", headers=headers)
            assert response.status_code == 200

            result = response.json()
            assert result["status"] == "authenticated"
            assert result["user_id"] == user_id
            assert result["username"] == username

    @pytest.mark.asyncio
    async def test_middleware_with_invalid_token(self, app, token_manager):
        """测试中间件使用无效 token 处理请求"""
        # 设置 Token 管理器
        set_token_manager(token_manager)

        # 注册中间件
        app.add_middleware(AuthMiddleware)

        # 使用 TestClient 测试
        with TestClient(app) as client:
            headers = {"Authorization": "Bearer invalid-token"}
            response = client.get("/protected", headers=headers)
            assert response.status_code == 200
            # 应该返回匿名状态，因为 token 无效
            assert response.json()["status"] == "anonymous"

    @pytest.mark.asyncio
    async def test_middleware_with_revoked_token(self, app, token_manager):
        """测试中间件使用已撤销 token 处理请求"""
        # 设置 Token 管理器
        set_token_manager(token_manager)

        # 创建用户 token
        user_id = 123
        username = "testuser"
        access_token = token_manager.create_access_token(user_id, username)

        # 撤销 token
        await token_manager.revoke_access_token(access_token)

        # 注册中间件
        app.add_middleware(AuthMiddleware)

        # 使用 TestClient 测试
        with TestClient(app) as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = client.get("/protected", headers=headers)
            assert response.status_code == 200
            # 应该返回匿名状态，因为 token 已被撤销
            assert response.json()["status"] == "anonymous"

    @pytest.mark.asyncio
    async def test_middleware_without_token_manager(self, app):
        """测试中间件在没有 Token 管理器的情况下处理请求"""
        # 不设置 Token 管理器

        # 注册中间件
        app.add_middleware(AuthMiddleware)

        # 使用 TestClient 测试
        with TestClient(app) as client:
            response = client.get("/protected")
            assert response.status_code == 200
            # 应该返回匿名状态，因为没有 Token 管理器
            assert response.json()["status"] == "anonymous"

    @pytest.mark.asyncio
    async def test_middleware_with_malformed_auth_header(self, app, token_manager):
        """测试中间件处理格式错误的 Authorization header"""
        # 设置 Token 管理器
        set_token_manager(token_manager)

        # 注册中间件
        app.add_middleware(AuthMiddleware)

        # 使用 TestClient 测试
        with TestClient(app) as client:
            # 格式错误的 header
            headers = {"Authorization": "InvalidFormat token"}
            response = client.get("/protected", headers=headers)
            assert response.status_code == 200
            # 应该返回匿名状态，因为格式错误
            assert response.json()["status"] == "anonymous"

    @pytest.mark.asyncio
    async def test_depends_uses_middleware_user_info(self, app, token_manager):
        """测试依赖函数使用中间件设置的 user_info"""
        from src.auth.dependencies import get_current_user
        from fastapi import Depends

        # 设置 Token 管理器
        set_token_manager(token_manager)

        # 创建用户 token
        user_id = 123
        username = "testuser"
        access_token = token_manager.create_access_token(user_id, username)

        @app.get("/auth-check")
        async def auth_check(current_user=Depends(get_current_user)):
            return {
                "user_id": current_user.id,
                "username": current_user.username,
            }

        # 注册中间件
        app.add_middleware(AuthMiddleware)

        # 使用 TestClient 测试
        with TestClient(app) as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = client.get("/auth-check", headers=headers)
            assert response.status_code == 200

            result = response.json()
            assert result["user_id"] == user_id
            assert result["username"] == username

    @pytest.mark.asyncio
    async def test_middleware_error_handling(self, app, token_manager):
        """测试中间件错误处理"""
        # 设置 Token 管理器
        set_token_manager(token_manager)

        # 注册中间件
        app.add_middleware(AuthMiddleware)

        # 使用 TestClient 测试
        with TestClient(app) as client:
            # 使用空 header
            headers = {"Authorization": ""}
            response = client.get("/protected", headers=headers)
            assert response.status_code == 200
            # 应该返回匿名状态，因为 header 为空
            assert response.json()["status"] == "anonymous"
