from sqlmodel import Field, Relationship, SQLModel

from .mixins import TimestampMixin
from .rbac import Role, UserRole


class User(SQLModel, TimestampMixin, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    email: str = Field(unique=True, index=True, max_length=320)
    hashed_password: str = Field(max_length=1024)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)

    roles: list["Role"] = Relationship(
        back_populates="users",
        link_model=UserRole,
    )
