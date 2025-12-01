import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.core.schemas.user import User, UserRole
from src.core.schemas.role import Role, Permission, RolePermission
from src.session import async_session_factory, init_db, close_db


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client() -> TestClient:
    """创建测试客户端"""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
async def test_db() -> AsyncGenerator[str, None]:
    """初始化测试数据库（会话级）"""
    # 使用临时数据库文件
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_file.close()

    db_url = f"sqlite+aiosqlite:///{db_file.name}"

    # 初始化数据库
    await init_db(db_url, echo=False)

    # 创建所有表 - 先用同步方式
    from sqlalchemy import text

    # 使用同步方式创建表
    sync_engine = create_engine(f"sqlite:///{db_file.name}")
    SQLModel.metadata.create_all(sync_engine)
    sync_engine.dispose()

    # 再用异步方式确保表存在
    async_engine = create_async_engine(db_url, echo=False)
    async with async_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    await async_engine.dispose()

    yield db_url

    # 清理
    await close_db()
    if os.path.exists(db_file.name):
        os.unlink(db_file.name)


@pytest.fixture
async def db_session(test_db: str) -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话（每个测试）"""
    # 重新初始化会话工厂，使用测试数据库
    await init_db(test_db, echo=False)

    async with async_session_factory() as session:
        yield session
        # 每个测试后回滚
        try:
            await session.rollback()
        except Exception:
            pass


import uuid


def generate_unique_name(prefix: str) -> str:
    """生成唯一名称"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """创建测试用户"""
    username = generate_unique_name("testuser")
    user = User(
        username=username,
        hashed_password="hashed_password_123",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    yield user
    # 清理
    try:
        await db_session.delete(user)
        await db_session.commit()
    except Exception:
        pass


@pytest.fixture
async def test_admin_user(db_session: AsyncSession) -> User:
    """创建管理员测试用户"""
    username = generate_unique_name("admin")
    user = User(
        username=username,
        hashed_password="hashed_password_123",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    yield user
    # 清理
    try:
        await db_session.delete(user)
        await db_session.commit()
    except Exception:
        pass


@pytest.fixture
async def test_role(db_session: AsyncSession) -> Role:
    """创建测试角色"""
    name = generate_unique_name("test_role")
    role = Role(
        name=name,
        description="测试角色",
        is_system=False,
    )
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    yield role
    # 清理
    try:
        await db_session.delete(role)
        await db_session.commit()
    except Exception:
        pass


@pytest.fixture
async def test_permission(db_session: AsyncSession) -> Permission:
    """创建测试权限"""
    code = generate_unique_name("test:permission")
    name = generate_unique_name("test_permission")
    permission = Permission(
        name=name,
        code=code,
        description="测试权限",
        resource="test",
        action="read",
    )
    db_session.add(permission)
    await db_session.commit()
    await db_session.refresh(permission)
    yield permission
    # 清理
    try:
        await db_session.delete(permission)
        await db_session.commit()
    except Exception:
        pass
