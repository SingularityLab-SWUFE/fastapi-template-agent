from datetime import UTC, datetime

from sqlmodel import Field, SQLModel

from src.shared.mixins import TimestampMixin


class User(SQLModel, TimestampMixin, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    email: str = Field(unique=True, index=True, max_length=320)
    hashed_password: str = Field(max_length=1024)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)


class OAuthAccount(SQLModel, table=True):
    # defined in fastapi_users_db_sqlalchemy.SQLAlchemyBaseOAuthAccountTable
    # use sqlmodel style to avoid Pydantic schema generation error
    __tablename__ = "oauth_accounts"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    oauth_name: str = Field(max_length=100, nullable=False, index=True)
    access_token: str = Field(max_length=1024, nullable=False)
    expires_at: int | None = Field(default=None, nullable=True)
    refresh_token: str | None = Field(default=None, max_length=1024, nullable=True)
    account_id: str = Field(max_length=320, nullable=False, index=True)
    account_email: str = Field(max_length=320, nullable=False)


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
