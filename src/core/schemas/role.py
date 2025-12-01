from typing import Optional
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel, Relationship


class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100, description="角色名称")
    description: Optional[str] = Field(
        default=None, max_length=255, description="角色描述"
    )
    is_system: bool = Field(
        default=False, description="是否为系统角色（不可删除）"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # 角色与用户的关联（级联删除）
    user_roles: list["UserRole"] = Relationship(
        back_populates="role",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    # 角色与权限的关联（级联删除）
    permissions: list["RolePermission"] = Relationship(
        back_populates="role",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"


class Permission(SQLModel, table=True):
    __tablename__ = "permissions"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100, description="权限名称")
    code: str = Field(unique=True, index=True, max_length=100, description="权限编码")
    description: Optional[str] = Field(
        default=None, max_length=255, description="权限描述"
    )
    resource: Optional[str] = Field(
        default=None, max_length=100, description="资源类型"
    )
    action: Optional[str] = Field(
        default=None, max_length=100, description="操作类型"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # 权限与角色的关联
    role_permissions: list["RolePermission"] = Relationship(back_populates="permission")

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, name='{self.name}')>"


# 角色权限关联表（多对多）
class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permissions"

    role_id: int = Field(foreign_key="roles.id", primary_key=True)
    permission_id: int = Field(foreign_key="permissions.id", primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="分配时间"
    )

    role: Role = Relationship(back_populates="permissions")
    permission: Permission = Relationship(back_populates="role_permissions")

    def __repr__(self) -> str:
        return (
            f"<RolePermission(role_id={self.role_id}, "
            f"permission_id={self.permission_id})>"
        )


# 为了支持循环导入，放在文件末尾
from .user import UserRole

