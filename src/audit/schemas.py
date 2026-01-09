from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Text
from sqlmodel import Field, SQLModel

from src.shared.mixins import now


class AuditAction(StrEnum):
    LOGIN = "login"
    LOGOUT = "logout"
    REFRESH = "refresh"
    REGISTER = "register"
    VERIFY_EMAIL = "verify_email"
    FORGOT_PASSWORD = "forgot_password"
    RESET_PASSWORD = "reset_password"
    PERMISSION_CHECK = "permission_check"
    ROLE_CHECK = "role_check"
    PROTECTED_RESOURCE_ACCESS = "protected_resource_access"


class AuditResult(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    GRANTED = "granted"
    DENIED = "denied"


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: int | None = Field(default=None, primary_key=True)
    occurred_at: datetime = Field(
        default_factory=now,
        sa_type=DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    request_id: str | None = Field(
        default=None,
        max_length=36,
        description="Request correlation ID - groups all audit logs from a single HTTP request",
    )
    actor_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    action: str = Field(nullable=False, max_length=64, index=True)
    resource_type: str | None = Field(default=None, max_length=64)
    resource_id: str | None = Field(default=None, sa_column=Column(Text))
    result: str = Field(nullable=False, max_length=32)
    user_agent: str | None = Field(default=None, sa_column=Column(Text))
    ip: str | None = Field(default=None, max_length=45)
    extra: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
