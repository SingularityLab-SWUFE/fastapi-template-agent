import pytest
from fastapi import Depends, FastAPI
from fastapi_users.password import PasswordHelper
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from src.auth import current_user
from src.auth.permissions import require_permissions
from src.core.schemas import Permission, Role, RolePermission, User, UserRole
from src.handlers import register_exception_handlers
from src.session import get_session


@pytest.fixture
async def session_maker():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield maker

    await engine.dispose()


@pytest.fixture
async def app(session_maker):
    async def override_get_session():
        async with session_maker() as session:
            yield session

    app = FastAPI()
    app.dependency_overrides[get_session] = override_get_session
    register_exception_handlers(app)

    @app.get("/articles")
    async def list_articles(user=Depends(require_permissions("article:read"))):
        return {"ok": True}

    yield app

    app.dependency_overrides.clear()


@pytest.fixture
async def client(app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


async def _create_user_with_perm(session: AsyncSession) -> User:
    helper = PasswordHelper()
    role = Role(name="editor", description="Editor role", is_system=False)
    perm = Permission(
        code="article:read",
        name="Article read",
        module="article",
        description="Read articles",
    )
    session.add_all([role, perm])
    await session.flush()
    session.add(RolePermission(role_id=role.id, permission_id=perm.id))

    user = User(
        username="editor_user",
        email="editor@example.com",
        hashed_password=helper.hash("password123"),
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )
    session.add(user)
    await session.flush()
    session.add(UserRole(user_id=user.id, role_id=role.id))
    await session.commit()
    await session.refresh(user)
    return user


async def _create_plain_user(session: AsyncSession) -> User:
    helper = PasswordHelper()
    user = User(
        username="plain_user",
        email="plain@example.com",
        hashed_password=helper.hash("password123"),
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def _create_superuser(session: AsyncSession) -> User:
    helper = PasswordHelper()
    user = User(
        username="boss",
        email="boss@example.com",
        hashed_password=helper.hash("password123"),
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_access_allowed_with_permission(app: FastAPI, client: AsyncClient, session_maker):
    async with session_maker() as session:
        user = await _create_user_with_perm(session)

    app.dependency_overrides[current_user] = lambda: user

    response = await client.get("/articles")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


@pytest.mark.asyncio
async def test_access_denied_without_permission(app: FastAPI, client: AsyncClient, session_maker):
    async with session_maker() as session:
        user = await _create_plain_user(session)

    app.dependency_overrides[current_user] = lambda: user

    response = await client.get("/articles")

    assert response.status_code == 403
    assert response.json()["code"] == 30001


@pytest.mark.asyncio
async def test_superuser_bypass_permissions(app: FastAPI, client: AsyncClient, session_maker):
    async with session_maker() as session:
        user = await _create_superuser(session)

    app.dependency_overrides[current_user] = lambda: user

    response = await client.get("/articles")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
