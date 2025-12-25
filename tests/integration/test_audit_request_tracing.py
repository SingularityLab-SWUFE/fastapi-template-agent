import pytest
from fastapi import APIRouter, Depends
from sqlalchemy import select

from src.auth import current_user
from src.auth.models import User
from src.audit.schemas import AuditAction, AuditLog, AuditResult


@pytest.fixture
def test_app_with_protected_route(test_client):
    from src.main import app

    router = APIRouter()

    @router.get("/test/protected")
    async def protected_route(user: User = Depends(current_user)):
        return {"user_id": user.id}

    app.include_router(router)

    return test_client


async def test_current_user_creates_audit_log(
    test_app_with_protected_route, test_user, test_db
):
    test_client = test_app_with_protected_route

    login_response = await test_client.post(
        "/auth/jwt/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    access_token = login_response.json()["access_token"]

    response = await test_client.get(
        "/test/protected",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200

    async with test_db() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == AuditAction.PROTECTED_RESOURCE_ACCESS,
                AuditLog.actor_id == test_user.id,
            )
        )
        audit_logs = result.scalars().all()

        assert len(audit_logs) > 0
        audit_log = audit_logs[-1]
        assert audit_log.result == AuditResult.SUCCESS
        assert audit_log.actor_id == test_user.id
        assert audit_log.extra is not None
        assert audit_log.extra["method"] == "GET"
        assert "/test/protected" in audit_log.extra["path"]


async def test_protected_resource_audit_includes_request_id(
    test_app_with_protected_route, test_user, test_db
):
    test_client = test_app_with_protected_route

    login_response = await test_client.post(
        "/auth/jwt/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    access_token = login_response.json()["access_token"]

    response = await test_client.get(
        "/test/protected",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200

    async with test_db() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == AuditAction.PROTECTED_RESOURCE_ACCESS,
                AuditLog.actor_id == test_user.id,
            )
        )
        audit_logs = result.scalars().all()

        assert len(audit_logs) > 0
        audit_log = audit_logs[-1]
        assert audit_log.request_id is not None
        assert isinstance(audit_log.request_id, str)
        assert len(audit_log.request_id) == 36


async def test_login_audit_without_request_id(test_client, test_user, test_db):
    response = await test_client.post(
        "/auth/jwt/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )

    assert response.status_code == 200

    async with test_db() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == AuditAction.LOGIN,
                AuditLog.actor_id == test_user.id,
            )
        )
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert audit_log.request_id is None


async def test_rbac_audit_includes_request_id(
    test_app_with_protected_route, test_user, test_db
):
    from src.auth import require_permissions
    from src.auth.models import Permission, RolePermission
    from src.main import app

    async with test_db() as session:
        perm = Permission(id=100, code="test:read", name="Test Read", module="test")
        session.add(perm)
        await session.commit()

        role_perm = RolePermission(role_id=1, permission_id=100)
        session.add(role_perm)
        await session.commit()

        from src.auth.models import UserRole

        user_role = UserRole(user_id=test_user.id, role_id=1)
        session.add(user_role)
        await session.commit()

    router = APIRouter()

    @router.get("/test/rbac")
    async def rbac_route(
        user: User = Depends(current_user),
        _perm=Depends(require_permissions("test:read")),
    ):
        return {"user_id": user.id}

    app.include_router(router)

    test_client = test_app_with_protected_route

    login_response = await test_client.post(
        "/auth/jwt/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    access_token = login_response.json()["access_token"]

    response = await test_client.get(
        "/test/rbac",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200

    async with test_db() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == AuditAction.PERMISSION_CHECK,
                AuditLog.actor_id == test_user.id,
            )
        )
        audit_logs = result.scalars().all()

        assert len(audit_logs) > 0
        audit_log = audit_logs[-1]
        assert audit_log.request_id is not None
        assert isinstance(audit_log.request_id, str)
        assert len(audit_log.request_id) == 36


async def test_concurrent_requests_have_unique_request_ids(
    test_app_with_protected_route, test_user, test_db
):
    import asyncio

    test_client = test_app_with_protected_route

    login_response = await test_client.post(
        "/auth/jwt/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    access_token = login_response.json()["access_token"]

    async def make_request():
        return await test_client.get(
            "/test/protected",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    responses = await asyncio.gather(*[make_request() for _ in range(5)])

    for response in responses:
        assert response.status_code == 200

    async with test_db() as session:
        result = await session.execute(
            select(AuditLog.request_id).where(
                AuditLog.action == AuditAction.PROTECTED_RESOURCE_ACCESS,
                AuditLog.actor_id == test_user.id,
                AuditLog.request_id.isnot(None),
            )
        )
        request_ids = [r[0] for r in result.all()]

        assert len(request_ids) >= 5
        recent_request_ids = request_ids[-5:]
        assert len(set(recent_request_ids)) == 5
