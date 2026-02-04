from sqlmodel import Field, SQLModel

from src.mixins import TimestampMixin


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
