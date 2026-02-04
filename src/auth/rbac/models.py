from datetime import UTC, datetime

from sqlmodel import Field, SQLModel

from src.mixins import TimestampMixin


class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    role_id: int = Field(foreign_key="roles.id", primary_key=True)
    assigned_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )


class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permissions"

    role_id: int = Field(foreign_key="roles.id", primary_key=True)
    permission_id: int = Field(foreign_key="permissions.id", primary_key=True)
    assigned_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )


class Role(SQLModel, TimestampMixin, table=True):
    __tablename__ = "roles"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    is_system: bool = Field(default=False)


class Permission(SQLModel, TimestampMixin, table=True):
    __tablename__ = "permissions"

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=150)
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=255)
    module: str = Field(max_length=100)
