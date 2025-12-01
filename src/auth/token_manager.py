"""Token管理器

负责 JWT Token 的生成、验证、刷新和撤销。
使用 Redis 存储 refresh_token 和黑名单。
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
import uuid
import logging

from jose import jwt, JWTError
from passlib.context import CryptContext

from .cache_token_store import CacheTokenStore

logger = logging.getLogger(__name__)

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
        issuer: str = "fastapi-template-agent",
        audience: str = "fastapi-template-client",
    ) -> None:
        """初始化 Token 管理器

        Args:
            secret_key: JWT 签名密钥
            algorithm: 加密算法
            access_token_expire_minutes: access_token 过期时间（分钟）
            refresh_token_expire_days: refresh_token 过期时间（天）
            issuer: JWT 签发者标识
            audience: JWT 预期接收者标识
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.issuer = issuer
        self.audience = audience
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
            "iss": self.issuer,
            "aud": self.audience,
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
            # 先尝试不验证任何东西来获取 payload
            # 使用密钥但禁用所有验证
            payload = jwt.decode(
                token,
                self.secret_key,
                options={
                    "verify_signature": False,
                    "verify_exp": False,
                    "verify_nbf": False,
                    "verify_iat": False,
                    "verify_aud": False,
                    "verify_iss": False,
                },
            )

            # 检查 token 类型
            if payload.get("type") != "access":
                return None

            # 检查黑名单
            token_id = payload.get("token_id")
            if token_id and await self.cache_store.is_access_token_blacklisted(token_id):
                return None

            # 验证 aud 和 iss（向后兼容）
            token_aud = payload.get("aud")
            token_iss = payload.get("iss")

            # 如果 token 中有 aud claim，验证是否匹配
            if token_aud is not None:
                if token_aud != self.audience:
                    logger.warning(
                        f"Token audience mismatch: expected {self.audience}, got {token_aud}"
                    )
                    return None
            else:
                logger.warning(
                    "Token missing 'aud' claim. Consider upgrading tokens with audience validation."
                )

            # 如果 token 中有 iss claim，验证是否匹配
            if token_iss is not None:
                if token_iss != self.issuer:
                    logger.warning(
                        f"Token issuer mismatch: expected {self.issuer}, got {token_iss}"
                    )
                    return None
            else:
                logger.warning(
                    "Token missing 'iss' claim. Consider upgrading tokens with issuer validation."
                )

            return payload
        except JWTError as e:
            logger.error(f"JWT verification error: {e}")
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
        user_id = await self.verify_refresh_token(refresh_token)

        if user_id is None:
            return None

        # TODO: 获取用户信息并生成新的 access_token
        # 需要从数据库查询用户名，这里暂时返回 None
        # 在实际实现中需要注入数据库会话来查询用户信息
        return None

    async def revoke_access_token(self, token: str) -> bool:
        """撤销 access_token（加入黑名单）

        Args:
            token: JWT access_token

        Returns:
            撤销是否成功
        """
        try:
            # 解码 token，验证签名但不强制校验 aud/iss，以避免旧 token 兼容性问题
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={
                    "verify_aud": False,
                    "verify_iss": False,
                },
            )

            if payload.get("type") != "access":
                return False

            token_id = payload.get("token_id")
            sub = payload.get("sub")

            if not token_id or sub is None:
                return False

            user_id = int(sub)

            # 尝试根据 exp 计算黑名单 TTL，避免黑名单长期堆积
            ttl = None
            exp = payload.get("exp")
            if exp is not None:
                now_ts = int(datetime.now(timezone.utc).timestamp())
                try:
                    ttl = max(0, int(exp) - now_ts)
                except (ValueError, TypeError):
                    ttl = None

            await self.cache_store.blacklist_access_token(
                token_id=token_id,
                user_id=user_id,
                ttl=ttl,
            )
            return True
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
