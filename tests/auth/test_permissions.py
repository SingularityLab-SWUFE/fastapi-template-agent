import pytest
from fastapi_users.password import PasswordHelper
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.permissions import PermissionService, owner_or_perm, require_permissions
from src.core.config import get_settings
from src.core.schemas import Permission, Role, RolePermission, User, UserRole
from src.exceptions import BusinessException


@pytest.mark.asyncio
async def test_get_user_permissions_with_role(test_db) -> None:
    settings = get_settings()
    async with test_db() as session:  # type: AsyncSession
        role = Role(name="editor", description="Editor role", is_system=False)
        permission = Permission(
            code="article:write",
            name="Article write",
            module="article",
            description="Can write articles",
        )
        session.add_all([role, permission])
        await session.flush()
        session.add(RolePermission(role_id=role.id, permission_id=permission.id))

        password_helper = PasswordHelper()
        user = User(
            username="perm_user",
            email="perm_user@example.com",
            hashed_password=password_helper.hash("password123"),
            is_active=True,
            is_verified=True,
            is_superuser=False,
        )
        session.add(user)
        await session.flush()
        session.add(UserRole(user_id=user.id, role_id=role.id))
        await session.commit()

        service = PermissionService(session, settings)
        perms = await service.get_user_permissions(user.id)

        assert "article:write" in perms


@pytest.mark.asyncio
async def test_require_permissions_denied_when_missing(test_db) -> None:
    settings = get_settings()
    async with test_db() as session:  # type: AsyncSession
        password_helper = PasswordHelper()
        user = User(
            username="no_perm",
            email="no_perm@example.com",
            hashed_password=password_helper.hash("password123"),
            is_active=True,
            is_verified=True,
            is_superuser=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        service = PermissionService(session, settings)
        dependency = require_permissions("demo:write")

        with pytest.raises(BusinessException):
            await dependency(user=user, service=service)


@pytest.mark.asyncio
async def test_owner_or_perm_allows_owner(test_db) -> None:
    settings = get_settings()
    async with test_db() as session:  # type: AsyncSession
        password_helper = PasswordHelper()
        user = User(
            username="owner_user",
            email="owner_user@example.com",
            hashed_password=password_helper.hash("password123"),
            is_active=True,
            is_verified=True,
            is_superuser=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        service = PermissionService(session, settings)

        class Resource:
            def __init__(self, owner_id: int):
                self.owner_id = owner_id

        resource = Resource(owner_id=user.id)

        dependency = owner_or_perm(lambda: resource, "resource:edit")
        result = await dependency(obj=resource, user=user, service=service)

        assert result is resource


@pytest.mark.asyncio
async def test_superuser_bypass(test_db) -> None:
    settings = get_settings()
    async with test_db() as session:  # type: AsyncSession
        password_helper = PasswordHelper()
        user = User(
            username="super_admin",
            email="super_admin@example.com",
            hashed_password=password_helper.hash("password123"),
            is_active=True,
            is_verified=True,
            is_superuser=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        service = PermissionService(session, settings)

        assert await service.check_permissions(user.id, ["any:perm"])
