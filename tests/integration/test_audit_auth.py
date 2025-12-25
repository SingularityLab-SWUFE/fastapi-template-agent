from sqlalchemy import select

from src.audit.schemas import AuditAction, AuditLog, AuditResult
from src.shared.errors import ErrorCode


async def test_login_success_creates_audit_log(test_client, test_user, test_db):
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
        assert audit_log.result == AuditResult.SUCCESS
        assert audit_log.actor_id == test_user.id
        assert audit_log.ip is not None


async def test_login_failure_creates_audit_log(test_client, test_user, test_db):
    response = await test_client.post(
        "/auth/jwt/login",
        data={"username": "test@example.com", "password": "wrongpassword"},
    )

    assert response.status_code == 401

    async with test_db() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == AuditAction.LOGIN,
                AuditLog.result == AuditResult.FAILURE,
            )
        )
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert audit_log.result == AuditResult.FAILURE
        assert audit_log.actor_id is None
        assert audit_log.extra is not None
        assert "username" in audit_log.extra


async def test_refresh_token_success_creates_audit_log(test_client, test_user, test_db):
    login_response = await test_client.post(
        "/auth/jwt/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = await test_client.post(
        "/auth/jwt/refresh", params={"refresh_token": refresh_token}
    )

    assert response.status_code == 200

    async with test_db() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == AuditAction.REFRESH,
                AuditLog.actor_id == test_user.id,
            )
        )
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert audit_log.result == AuditResult.SUCCESS
        assert audit_log.actor_id == test_user.id


async def test_refresh_token_failure_creates_audit_log(test_client, test_db):
    response = await test_client.post(
        "/auth/jwt/refresh", params={"refresh_token": "invalid_token"}
    )

    assert response.status_code == 401

    async with test_db() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == AuditAction.REFRESH,
                AuditLog.result == AuditResult.FAILURE,
            )
        )
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert audit_log.result == AuditResult.FAILURE
        assert audit_log.actor_id is None


async def test_refresh_token_inactive_user_creates_audit_log(
    test_client, test_user, test_db
):
    from src.auth.models import User

    login_response = await test_client.post(
        "/auth/jwt/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    async with test_db() as session:
        user = await session.get(User, test_user.id)
        user.is_active = False
        session.add(user)
        await session.commit()

    response = await test_client.post(
        "/auth/jwt/refresh", params={"refresh_token": refresh_token}
    )

    assert response.status_code == 403
    assert response.json()["code"] == ErrorCode.USER_INACTIVE

    async with test_db() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == AuditAction.REFRESH,
                AuditLog.result == AuditResult.FAILURE,
                AuditLog.actor_id == test_user.id,
            )
        )
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert audit_log.result == AuditResult.FAILURE


async def test_logout_creates_audit_log(test_client, test_user, test_db):
    login_response = await test_client.post(
        "/auth/jwt/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = await test_client.post(
        "/auth/jwt/logout", params={"refresh_token": refresh_token}
    )

    assert response.status_code == 200

    async with test_db() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == AuditAction.LOGOUT,
                AuditLog.actor_id == test_user.id,
            )
        )
        audit_log = result.scalar_one_or_none()

        assert audit_log is not None
        assert audit_log.result == AuditResult.SUCCESS
        assert audit_log.actor_id == test_user.id
