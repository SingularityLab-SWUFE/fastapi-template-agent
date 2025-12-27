import pytest
from fastapi import APIRouter, Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from src.auth import require_permissions, require_roles
from src.auth.models import User
from src.audit.schemas import AuditAction, AuditLog, AuditResult
from src.shared.errors import ErrorCode
from src.auth.models import Permission, RolePermission, UserRole


@pytest.fixture
async def rbac_data(test_db):
    async with test_db() as session:
        perm_read = Permission(id=1, code="user:read", name="Read Users", module="user")
        perm_write = Permission(
            id=2, code="user:write", name="Write Users", module="user"
        )
        session.add_all([perm_read, perm_write])
        await session.commit()

        role_perms = [
            RolePermission(role_id=1, permission_id=1),
            RolePermission(role_id=1, permission_id=2),
            RolePermission(role_id=2, permission_id=1),
        ]
        session.add_all(role_perms)
        await session.commit()


@pytest.fixture
async def admin_user(test_db, rbac_data):
    from fastapi_users.password import PasswordHelper

    password_helper = PasswordHelper()
    hashed_password = password_helper.hash("admin123")

    async with test_db() as session:
        user = User(
            username="adminuser",
            email="admin@example.com",
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,
            is_superuser=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        user_role = UserRole(user_id=user.id, role_id=1)
        session.add(user_role)
        await session.commit()

        yield user


@pytest.fixture
async def regular_user(test_db, rbac_data):
    from fastapi_users.password import PasswordHelper

    password_helper = PasswordHelper()
    hashed_password = password_helper.hash("user123")

    async with test_db() as session:
        user = User(
            username="regularuser",
            email="user@example.com",
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,
            is_superuser=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        user_role = UserRole(user_id=user.id, role_id=2)
        session.add(user_role)
        await session.commit()

        yield user


@pytest.fixture
async def superuser_user(test_db, rbac_data):
    from fastapi_users.password import PasswordHelper

    password_helper = PasswordHelper()
    hashed_password = password_helper.hash("super123")

    async with test_db() as session:
        user = User(
            username="superuser",
            email="super@example.com",
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,
            is_superuser=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        yield user


@pytest.fixture
async def rbac_audit_client(
    test_db, local_cache, admin_user, regular_user, superuser_user
):
    from src.api import auth_router
    from src.cache import get_cache
    from src.handlers import register_exception_handlers
    from src.responses.middleware import ResponseWrapperMiddleware
    from src.session import get_session

    app = FastAPI()
    app.add_middleware(ResponseWrapperMiddleware)
    register_exception_handlers(app)

    async def override_get_session():
        async with test_db() as session:
            yield session

    async def override_get_cache():
        yield local_cache

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_cache] = override_get_cache

    app.include_router(auth_router, prefix="/auth")

    router = APIRouter()

    @router.get(
        "/perm-write", dependencies=[Depends(require_permissions("user:write"))]
    )
    async def perm_write():
        return {"message": "access granted"}

    @router.get("/role-admin", dependencies=[Depends(require_roles("admin"))])
    async def role_admin():
        return {"message": "access granted"}

    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


async def get_auth_headers(client: AsyncClient, email: str, password: str) -> dict:
    response = await client.post(
        "/auth/jwt/login",
        data={"username": email, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_permission_check_granted_creates_audit_log(
    rbac_audit_client, admin_user, test_db
):
    headers = await get_auth_headers(rbac_audit_client, "admin@example.com", "admin123")
    response = await rbac_audit_client.get("/perm-write", headers=headers)

    assert response.status_code == 200

    async with test_db() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == AuditAction.PERMISSION_CHECK,
                AuditLog.actor_id == admin_user.id,
                AuditLog.result == AuditResult.GRANTED,
            )
        )
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert audit_log.result == AuditResult.GRANTED
        assert audit_log.actor_id == admin_user.id
        assert audit_log.extra is not None
        assert "permissions" in audit_log.extra
        assert "user:write" in audit_log.extra["permissions"]


@pytest.mark.asyncio
async def test_permission_check_denied_creates_audit_log(
    rbac_audit_client, regular_user, test_db
):
    headers = await get_auth_headers(rbac_audit_client, "user@example.com", "user123")
    response = await rbac_audit_client.get("/perm-write", headers=headers)

    assert response.status_code == 403
    assert response.json()["code"] == ErrorCode.PERM_INSUFFICIENT

    async with test_db() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == AuditAction.PERMISSION_CHECK,
                AuditLog.actor_id == regular_user.id,
                AuditLog.result == AuditResult.DENIED,
            )
        )
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert audit_log.result == AuditResult.DENIED
        assert audit_log.actor_id == regular_user.id
        assert audit_log.extra is not None
        assert "permissions" in audit_log.extra
        assert "user:write" in audit_log.extra["permissions"]


@pytest.mark.asyncio
async def test_role_check_granted_creates_audit_log(
    rbac_audit_client, admin_user, test_db
):
    headers = await get_auth_headers(rbac_audit_client, "admin@example.com", "admin123")
    response = await rbac_audit_client.get("/role-admin", headers=headers)

    assert response.status_code == 200

    async with test_db() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == AuditAction.ROLE_CHECK,
                AuditLog.actor_id == admin_user.id,
                AuditLog.result == AuditResult.GRANTED,
            )
        )
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert audit_log.result == AuditResult.GRANTED
        assert audit_log.actor_id == admin_user.id
        assert audit_log.extra is not None
        assert "roles" in audit_log.extra
        assert "admin" in audit_log.extra["roles"]


@pytest.mark.asyncio
async def test_role_check_denied_creates_audit_log(
    rbac_audit_client, regular_user, test_db
):
    headers = await get_auth_headers(rbac_audit_client, "user@example.com", "user123")
    response = await rbac_audit_client.get("/role-admin", headers=headers)

    assert response.status_code == 403
    assert response.json()["code"] == ErrorCode.ROLE_INSUFFICIENT

    async with test_db() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == AuditAction.ROLE_CHECK,
                AuditLog.actor_id == regular_user.id,
                AuditLog.result == AuditResult.DENIED,
            )
        )
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert audit_log.result == AuditResult.DENIED
        assert audit_log.actor_id == regular_user.id
        assert audit_log.extra is not None
        assert "roles" in audit_log.extra
        assert "admin" in audit_log.extra["roles"]


@pytest.mark.asyncio
async def test_superuser_without_permission_denied_creates_audit_log(
    rbac_audit_client, superuser_user, test_db
):
    headers = await get_auth_headers(rbac_audit_client, "super@example.com", "super123")
    response = await rbac_audit_client.get("/perm-write", headers=headers)

    assert response.status_code == 403

    async with test_db() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == AuditAction.PERMISSION_CHECK,
                AuditLog.actor_id == superuser_user.id,
                AuditLog.result == AuditResult.DENIED,
            )
        )
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert audit_log.result == AuditResult.DENIED
