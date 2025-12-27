from pathlib import Path
from typing import AsyncGenerator

import dotenv
import pytest
from fakeredis import FakeAsyncRedis
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from migrations.seed_data import insert_rbac_seed_data_async
from src.cache import LocalCache, RedisCache
from src.main import app
from src.session import get_session

env_path = Path(__file__).parent.parent / ".env-example"
dotenv.load_dotenv(dotenv_path=env_path)


@pytest.fixture
def settings():
    from src.config import get_settings

    return get_settings()


@pytest.fixture(autouse=True)
def disable_logging():
    logger.disable("src")
    yield
    logger.enable("src")


@pytest.fixture
def base_app() -> FastAPI:
    return FastAPI()


@pytest.fixture
def app_with_middleware(base_app: FastAPI) -> FastAPI:
    from src.responses import ResponseWrapperMiddleware

    base_app.add_middleware(ResponseWrapperMiddleware)
    return base_app


@pytest.fixture
def app_with_handlers(base_app: FastAPI) -> FastAPI:
    from src.handlers import register_exception_handlers

    register_exception_handlers(base_app)
    return base_app


@pytest.fixture
def full_app(base_app: FastAPI) -> FastAPI:
    from src.responses import ResponseWrapperMiddleware
    from src.handlers import register_exception_handlers

    base_app.add_middleware(ResponseWrapperMiddleware)
    register_exception_handlers(base_app)
    return base_app


@pytest.fixture
async def async_client(full_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=full_app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
async def test_db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.connect() as conn:
        await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.commit()

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with engine.connect() as conn:
        await insert_rbac_seed_data_async(conn)

    async def override_get_session():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    yield async_session

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    app.dependency_overrides.clear()


@pytest.fixture
async def local_cache():
    cache = LocalCache()
    yield cache
    await cache.close()


@pytest.fixture
async def redis_cache():
    cache = RedisCache(host="localhost", port=6379, db=1)
    cache._client = FakeAsyncRedis(decode_responses=True)
    await cache.clear()
    yield cache
    await cache.clear()
    await cache.close()


@pytest.fixture
async def test_user(test_db):
    from fastapi_users.password import PasswordHelper

    from src.auth.models import User

    password_helper = PasswordHelper()
    hashed_password = password_helper.hash("testpassword123")

    async with test_db() as session:
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,
            is_superuser=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        yield user


@pytest.fixture
async def test_client(test_db, local_cache):
    from src.cache import get_cache

    async def override_get_cache():
        yield local_cache

    app.dependency_overrides[get_cache] = override_get_cache

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    del app.dependency_overrides[get_cache]
