import pytest
from fastapi_users.password import PasswordHelper

from src.auth.models import User
from src.auth.rbac.models import Permission, RolePermission, UserRole


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
