"""Test custom JWT authentication routes.

Standard fastapi-users routes (/register, /reset-password, /verify, /users)
are tested by the library itself and not duplicated here.
"""

from src.shared.errors import ErrorCode


async def test_login_success(test_client, test_user):
    response = await test_client.post(
        "/auth/jwt/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"


async def test_login_invalid_credentials(test_client, test_user):
    response = await test_client.post(
        "/auth/jwt/login",
        data={"username": "test@example.com", "password": "wrongpassword"},
    )

    assert response.status_code == 401
    data = response.json()
    assert data["msg"] == "Invalid credentials"
    assert data["code"] == ErrorCode.AUTH_INVALID_CREDENTIALS


async def test_login_nonexistent_user(test_client):
    response = await test_client.post(
        "/auth/jwt/login",
        data={"username": "nonexistent@example.com", "password": "password"},
    )

    assert response.status_code == 401
    assert response.json()["code"] == ErrorCode.AUTH_INVALID_CREDENTIALS


async def test_refresh_token_success(test_client, test_user):
    login_response = await test_client.post(
        "/auth/jwt/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = await test_client.post(
        "/auth/jwt/refresh", params={"refresh_token": refresh_token}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert "refresh_token" not in data


async def test_refresh_token_invalid(test_client):
    response = await test_client.post(
        "/auth/jwt/refresh", params={"refresh_token": "invalid_token"}
    )

    assert response.status_code == 401
    data = response.json()
    assert data["msg"] == "Invalid token"
    assert data["code"] == ErrorCode.AUTH_TOKEN_INVALID


async def test_logout_success(test_client, test_user):
    login_response = await test_client.post(
        "/auth/jwt/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = await test_client.post(
        "/auth/jwt/logout", params={"refresh_token": refresh_token}
    )

    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully logged out"

    refresh_response = await test_client.post(
        "/auth/jwt/refresh", params={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 401
    assert refresh_response.json()["code"] == ErrorCode.AUTH_TOKEN_INVALID


async def test_refresh_token_inactive_user(test_client, test_user, test_db):
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
    data = response.json()
    assert data["msg"] == "User inactive"
    assert data["code"] == ErrorCode.USER_INACTIVE


async def test_reset_password_revokes_tokens(test_client, test_user, local_cache):
    from src.auth.backend import RefreshTokenManager
    from src.config import get_settings

    settings = get_settings()
    login_response = await test_client.post(
        "/auth/jwt/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    refresh_manager = RefreshTokenManager(local_cache, settings)
    await refresh_manager.revoke_all_user_tokens(test_user.id)

    response = await test_client.post(
        "/auth/jwt/refresh", params={"refresh_token": refresh_token}
    )

    assert response.status_code == 401
    assert response.json()["code"] == ErrorCode.AUTH_TOKEN_INVALID
