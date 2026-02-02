from datetime import datetime, timedelta, timezone

from sqlalchemy import DateTime
from sqlmodel import Field


def get_timezone() -> timezone:
    """Get configured timezone, defaults to UTC+8 if not configured"""
    try:
        from src.config import get_settings

        tz_offset = get_settings().app.timezone
        return timezone(timedelta(hours=tz_offset))
    except ImportError:
        return timezone(timedelta(hours=8))


def now() -> datetime:
    """Get current datetime with configured timezone"""
    return datetime.now(get_timezone())


class TimestampMixin:
    created_at: datetime = Field(
        default_factory=now,
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": now},
    )
