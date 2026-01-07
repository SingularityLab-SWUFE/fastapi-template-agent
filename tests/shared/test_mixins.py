from asyncio import sleep

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Field, SQLModel

from src.shared.mixins import TimestampMixin


class SampleModel(SQLModel, TimestampMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str


@pytest.fixture
async def mixin_db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield async_session

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


async def test_timestamp_mixin_updated_at_updates(mixin_db):
    async with mixin_db() as session:
        record = SampleModel(name="original")
        session.add(record)
        await session.commit()
        await session.refresh(record)
        initial_updated_at = record.updated_at

        await sleep(0.01)

        record.name = "modified"
        session.add(record)
        await session.commit()
        await session.refresh(record)

        assert record.updated_at > initial_updated_at


async def test_timestamp_mixin_created_at_unchanged(mixin_db):
    async with mixin_db() as session:
        record = SampleModel(name="original")
        session.add(record)
        await session.commit()
        await session.refresh(record)
        initial_created_at = record.created_at

        await sleep(0.01)

        record.name = "modified"
        session.add(record)
        await session.commit()
        await session.refresh(record)

        assert record.created_at == initial_created_at
