"""Token管理器

负责 JWT Token 的生成、验证、刷新和撤销。
使用 Redis 存储 refresh_token 和黑名单。
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
import uuid

from jose import jwt, JWTError
from passlib.context import CryptContext

from .cache_token_store import CacheTokenStore

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenManager:
    """JWT Token 管理器"""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ) -> None:
        """初始化 Token 管理器

        Args:
            secret_key: JWT 签名密钥
            algorithm: 加密算法
            access_token_expire_minutes: access_token 过期时间（分钟）
            refresh_token_expire_days: refresh_token 过期时间（天）
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.cache_store = CacheTokenStore()

    def create_access_token(
        self, user_id: int, username: str, **extra_data: Any
    ) -> str:
        """创建 access_token

        Args:
            user_id: 用户 ID
            username: 用户名
            **extra_data: 额外数据

        Returns:
            JWT access_token 字符串
        """
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self.access_token_expire_minutes
        )

        payload: Dict[str, Any] = {
            "sub": str(user_id),
            "username": username,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
            "token_id": str(uuid.uuid4()),
        }

        payload.update(extra_data)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    async def create_refresh_token(self, user_id: int) -> str:
        """创建 refresh_token

        Args:
            user_id: 用户 ID

        Returns:
            UUID 格式的 refresh_token 字符串
        """
        token_id = str(uuid.uuid4())
        expire = datetime.now(timezone.utc) + timedelta(
            days=self.refresh_token_expire_days
        )

        # 将 refresh_token 存储到 Redis
        await self.cache_store.store_refresh_token(
            token_id=token_id, user_id=user_id, expires_at=int(expire.timestamp())
        )

        return token_id

    async def create_token_pair(self, user_id: int, username: str) -> Dict[str, str]:
        """创建 access_token 和 refresh_token 对

        Args:
            user_id: 用户 ID
            username: 用户名

        Returns:
            包含 access_token 和 refresh_token 的字典
        """
        access_token = self.create_access_token(user_id, username)
        refresh_token = await self.create_refresh_token(user_id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证 access_token

        Args:
            token: JWT access_token

        Returns:
            解码后的 payload，如果无效则返回 None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # 检查 token 类型
            if payload.get("type") != "access":
                return None

            # 检查黑名单
            token_id = payload.get("token_id")
            if token_id and await self.cache_store.is_access_token_blacklisted(token_id):
                return None

            return payload
        except JWTError:
            return None

    async def verify_refresh_token(self, token: str) -> Optional[int]:
        """验证 refresh_token

        Args:
            token: refresh_token ID

        Returns:
            用户 ID，如果无效则返回 None
        """
        return await self.cache_store.get_refresh_token_user_id(token)

    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """使用 refresh_token 获取新的 access_token

        Args:
            refresh_token: refresh_token ID

        Returns:
            新的 access_token，如果 refresh_token 无效则返回 None
        """
        user_id = self.verify_refresh_token(refresh_token)

        if user_id is None:
            return None

        # 获取用户信息（这里需要从数据库获取，实际使用时通过依赖注入）
        # 在使用时通过 get_current_user 获取用户信息
        return None

    async def revoke_access_token(self, token: str) -> bool:
        """撤销 access_token（加入黑名单）

        Args:
            token: JWT access_token

        Returns:
            撤销是否成功
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            if payload.get("type") != "access":
                return False

            token_id = payload.get("token_id")
            user_id = int(payload.get("sub"))

            if token_id:
                await self.cache_store.blacklist_access_token(
                    token_id=token_id, user_id=user_id
                )
                return True

            return False
        except (JWTError, ValueError, TypeError):
            return False

    async def revoke_refresh_token(self, token: str) -> bool:
        """撤销 refresh_token

        Args:
            token: refresh_token ID

        Returns:
            撤销是否成功
        """
        return await self.cache_store.delete_refresh_token(token)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码

        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码

        Returns:
            密码是否匹配
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """获取密码哈希

        Args:
            password: 明文密码

        Returns:
            哈希后的密码
        """
        return pwd_context.hash(password)
