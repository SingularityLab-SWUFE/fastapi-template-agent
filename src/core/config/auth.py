"""认证配置

JWT Token 相关配置参数。
"""

from pydantic import BaseModel, Field
from typing import Optional
from pydantic import ConfigDict


class JWTSettings(BaseModel):
    """JWT 配置"""

    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        description="JWT 签名密钥",
    )
    algorithm: str = Field(
        default="HS256",
        description="加密算法",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        description="access_token 过期时间（分钟）",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        description="refresh_token 过期时间（天）",
    )
    issuer: str = Field(
        default="fastapi-template-agent",
        description="JWT 签发者标识",
    )
    audience: str = Field(
        default="fastapi-template-client",
        description="JWT 预期接收者标识",
    )

    model_config = ConfigDict(env_prefix="JWT_")


# 全局 JWT 设置实例
jwt_settings = JWTSettings()
