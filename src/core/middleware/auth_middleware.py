"""认证中间件

全局解析 Authorization header，自动验证 JWT token 并设置 request.state.user。
提供类似 sa-token 的全局过滤体验。
"""

from typing import Optional, Callable, Any, Dict
import logging

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.auth.token_manager import TokenManager
from src.auth.dependencies import _get_token_manager
from src.core.schemas.user import User

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件

    自动解析 Authorization header，验证 JWT token，并将用户信息设置到 request.state.user。
    减少重复 token 验证，提升性能。
    """

    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        """初始化认证中间件

        Args:
            app: ASGI 应用
        """
        super().__init__(app)
        self._token_manager: Optional[TokenManager] = None

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Any]
    ) -> Any:
        """处理请求

        解析 Authorization header，验证 token，设置 request.state.user。
        注意：这里不抛出异常，让依赖函数处理认证失败的情况。

        Args:
            request: FastAPI 请求对象
            call_next: 下一个处理函数

        Returns:
            响应对象
        """
        # 获取 Token 管理器
        try:
            token_manager = _get_token_manager()
        except RuntimeError:
            # Token 管理器未初始化，跳过认证
            return await call_next(request)

        # 跳过认证的路径（如登录、文档等）
        if await self._should_skip_auth(request):
            return await call_next(request)

        # 解析 Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # 没有 token，不设置 user，继续处理
            # 依赖函数会处理认证失败的情况
            return await call_next(request)

        token = auth_header.split(" ")[1]

        try:
            # 验证 access_token
            payload = await token_manager.verify_access_token(token)

            if payload:
                # 解析用户信息
                user_id = payload.get("sub")
                username = payload.get("username")

                if user_id and username:
                    # 创建用户对象（简化版，仅包含必要信息）
                    # 完整用户信息仍需通过依赖函数从数据库获取
                    user_info = {
                        "id": int(user_id),
                        "username": username,
                    }

                    # 设置到 request.state
                    request.state.user_info = user_info

        except Exception as e:
            # 记录错误但不中断请求
            logger.error(f"Auth middleware error: {e}")

        # 继续处理请求
        response = await call_next(request)
        return response

    async def _should_skip_auth(self, request: Request) -> bool:
        """判断是否应该跳过认证

        Args:
            request: FastAPI 请求对象

        Returns:
            是否跳过认证
        """
        path = request.url.path

        # 跳过认证的路径
        skip_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
        ]

        return any(path.startswith(skip_path) for skip_path in skip_paths)
