import pytest
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient

from src.auth import owner_or_perm, require_permissions, require_roles
from src.auth.models import User
from src.shared.errors import ErrorCode
from src.auth.models import Permission, RolePermission, UserRole


@pytest.fixture
async def rbac_data(test_db):
    async with test_db() as session:
        perm_read = Permission(id=1, code="user:read", name="Read Users", module="user")
        perm_write = Permission(
            id=2, code="user:write", name="Write Users", module="user"
        )
        perm_delete = Permission(
            id=3, code="user:delete", name="Delete Users", module="user"
        )
        perm_admin_all = Permission(
            id=4, code="admin:*", name="Admin All", module="admin"
        )
        session.add_all([perm_read, perm_write, perm_delete, perm_admin_all])
        await session.commit()

        role_perms = [
            RolePermission(role_id=1, permission_id=1),
            RolePermission(role_id=1, permission_id=2),
            RolePermission(role_id=1, permission_id=3),
            RolePermission(role_id=1, permission_id=4),
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
async def rbac_client(test_db, local_cache, admin_user, regular_user, superuser_user):
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

    @router.get(
        "/perm-any",
        dependencies=[
            Depends(require_permissions("user:write", "user:delete", match="any"))
        ],
    )
    async def perm_any():
        return {"message": "access granted"}

    @router.get("/role-admin", dependencies=[Depends(require_roles("admin"))])
    async def role_admin():
        return {"message": "access granted"}

    @router.get(
        "/role-any",
        dependencies=[Depends(require_roles("admin", "moderator", match="any"))],
    )
    async def role_any():
        return {"message": "access granted"}

    async def get_resource_owner_id(resource_id: int) -> int:
        return resource_id

    @router.get(
        "/resources/{resource_id}",
        dependencies=[Depends(owner_or_perm(get_resource_owner_id, ["user:delete"]))],
    )
    async def resource(resource_id: int):
        return {"message": f"access to resource {resource_id}"}

    async def get_resource_owner_id_not_found(resource_id: int) -> int:
        raise HTTPException(status_code=404, detail="Resource not found")

    @router.get(
        "/resources-bypass/{resource_id}",
        dependencies=[
            Depends(
                owner_or_perm(
                    get_resource_owner_id_not_found,
                    ["user:delete"],
                    bypass_superuser=True,
                )
            )
        ],
    )
    async def resource_bypass(resource_id: int):
        return {"message": f"access to resource {resource_id}"}

    @router.get(
        "/resources-no-bypass/{resource_id}",
        dependencies=[
            Depends(
                owner_or_perm(
                    get_resource_owner_id_not_found,
                    ["user:delete"],
                    bypass_superuser=False,
                )
            )
        ],
    )
    async def resource_no_bypass(resource_id: int):
        return {"message": f"access to resource {resource_id}"}

    @router.get(
        "/perm-wildcard",
        dependencies=[Depends(require_permissions("admin:read"))],
    )
    async def perm_wildcard():
        return {"message": "access granted"}

    @router.get(
        "/perm-wildcard-disabled",
        dependencies=[
            Depends(require_permissions("admin:read", wildcard_support=False))
        ],
    )
    async def perm_wildcard_disabled():
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


@pytest.mark.parametrize(
    "endpoint,user_email,user_password,expected_status,expected_code",
    [
        ("/perm-write", "admin@example.com", "admin123", 200, None),
        (
            "/perm-write",
            "user@example.com",
            "user123",
            403,
            ErrorCode.PERM_INSUFFICIENT,
        ),
        ("/perm-any", "admin@example.com", "admin123", 200, None),
        ("/perm-any", "user@example.com", "user123", 403, ErrorCode.PERM_INSUFFICIENT),
        ("/role-admin", "admin@example.com", "admin123", 200, None),
        (
            "/role-admin",
            "user@example.com",
            "user123",
            403,
            ErrorCode.ROLE_INSUFFICIENT,
        ),
        ("/role-any", "admin@example.com", "admin123", 200, None),
    ],
)
@pytest.mark.asyncio
async def test_rbac_dependencies(
    rbac_client,
    admin_user,
    regular_user,
    endpoint,
    user_email,
    user_password,
    expected_status,
    expected_code,
):
    headers = await get_auth_headers(rbac_client, user_email, user_password)
    response = await rbac_client.get(endpoint, headers=headers)

    assert response.status_code == expected_status
    if expected_code:
        assert response.json()["code"] == expected_code


@pytest.mark.parametrize(
    "use_owner_resource,user_email,user_password,expected_status,expected_code",
    [
        (True, "user@example.com", "user123", 200, None),
        (False, "admin@example.com", "admin123", 200, None),
        (False, "user@example.com", "user123", 403, ErrorCode.PERM_INSUFFICIENT),
    ],
)
@pytest.mark.asyncio
async def test_owner_or_perm_dependency(
    rbac_client,
    admin_user,
    regular_user,
    use_owner_resource,
    user_email,
    user_password,
    expected_status,
    expected_code,
):
    resource_id = regular_user.id if use_owner_resource else admin_user.id
    headers = await get_auth_headers(rbac_client, user_email, user_password)
    response = await rbac_client.get(f"/resources/{resource_id}", headers=headers)

    assert response.status_code == expected_status
    if expected_code:
        assert response.json()["code"] == expected_code


@pytest.mark.asyncio
async def test_owner_or_perm_bypass_superuser_skips_owner_lookup(rbac_client):
    headers = await get_auth_headers(rbac_client, "super@example.com", "super123")
    response = await rbac_client.get("/resources-bypass/999", headers=headers)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_owner_or_perm_no_bypass_superuser_does_not_skip_owner_lookup(
    rbac_client,
):
    headers = await get_auth_headers(rbac_client, "super@example.com", "super123")
    response = await rbac_client.get("/resources-no-bypass/999", headers=headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_require_permissions_wildcard_enabled_allows_module_wildcard(rbac_client):
    headers = await get_auth_headers(rbac_client, "admin@example.com", "admin123")
    response = await rbac_client.get("/perm-wildcard", headers=headers)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_require_permissions_wildcard_disabled_denies_module_wildcard(
    rbac_client,
):
    headers = await get_auth_headers(rbac_client, "admin@example.com", "admin123")
    response = await rbac_client.get("/perm-wildcard-disabled", headers=headers)

    assert response.status_code == 403
    assert response.json()["code"] == ErrorCode.PERM_INSUFFICIENT
