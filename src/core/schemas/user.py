from typing import Optional
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel, Relationship

from .mixins import TimestampMixin


class User(SQLModel, TimestampMixin, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    hashed_password: str = Field(max_length=255)
    is_active: bool = Field(default=True, description="用户是否活跃")
    is_superuser: bool = Field(default=False, description="是否为超级用户")

    # 用户与角色的关联
    roles: list["UserRole"] = Relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', is_active={self.is_active})>"


# 用户角色关联表（多对多）
class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    role_id: int = Field(foreign_key="roles.id", primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="分配时间"
    )

    user: "User" = Relationship(back_populates="roles")
    role: "Role" = Relationship(back_populates="user_roles")
