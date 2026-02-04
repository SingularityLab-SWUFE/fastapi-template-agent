from datetime import UTC, datetime

from sqlmodel import Field


class TimestampMixin:
    """Provides UTC timestamp fields for models.

    Principle: Store in UTC, query in UTC, convert to local time at presentation time.

    For display in local timezone, convert using settings.app.timezone
    in the presentation layer (Pydantic serializers, API responses).
    """

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )
