import pytest
from unittest.mock import AsyncMock, MagicMock

from src.auth.rbac import PermissionRepository, PermissionService


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def permission_service(mock_session):
    repository = PermissionRepository(mock_session)
    return PermissionService(mock_session, repository=repository)


@pytest.mark.asyncio
async def test_get_user_permissions(mock_session, permission_service):
    user_id = 1
    mock_session.execute.return_value.scalars = MagicMock(
        return_value=MagicMock(all=MagicMock(return_value=["user:read", "user:write"]))
    )

    result = await permission_service.get_user_permissions(user_id)

    assert result == {"user:read", "user:write"}


@pytest.mark.parametrize(
    "user_perms,required_perms,match,expected",
    [
        ({"user:read", "user:write"}, ["user:read", "user:write"], "all", True),
        ({"user:read"}, ["user:read", "user:write"], "any", True),
    ],
)
@pytest.mark.asyncio
async def test_check_permissions_match(
    permission_service, user_perms, required_perms, match, expected
):
    user_id = 1
    permission_service.get_user_permissions = AsyncMock(return_value=user_perms)

    result = await permission_service.check_permissions(
        user_id=user_id, required_perms=required_perms, match=match
    )

    assert result is expected


@pytest.mark.parametrize(
    "user_perms,required_perms,wildcard_support,expected",
    [
        ({"user:read", "user:write"}, ["user:*"], True, True),
        ({"user:*"}, ["user:read"], True, True),
        ({"user:read", "user:*"}, ["user:"], True, False),
        ({"user:read"}, ["user:"], False, False),
    ],
)
@pytest.mark.asyncio
async def test_check_permissions_wildcard(
    permission_service, user_perms, required_perms, wildcard_support, expected
):
    user_id = 1
    permission_service.get_user_permissions = AsyncMock(return_value=user_perms)

    result = await permission_service.check_permissions(
        user_id=user_id,
        required_perms=required_perms,
        match="all",
        wildcard_support=wildcard_support,
    )

    assert result is expected


@pytest.mark.parametrize(
    "user_perms,required_perms,wildcard_support,expected",
    [
        ({"user:read"}, [""], True, True),
        ({"user:read"}, [""], False, False),
        ({"user:read", "user:*"}, ["user:"], True, False),
        ({"user:read"}, ["user:"], False, False),
    ],
)
@pytest.mark.asyncio
async def test_check_permissions_empty_and_trailing_colon(
    permission_service, user_perms, required_perms, wildcard_support, expected
):
    user_id = 1
    permission_service.get_user_permissions = AsyncMock(return_value=user_perms)

    result = await permission_service.check_permissions(
        user_id=user_id,
        required_perms=required_perms,
        match="all",
        wildcard_support=wildcard_support,
    )

    assert result is expected


@pytest.mark.asyncio
async def test_check_permissions_global_wildcard(permission_service):
    user_id = 1
    permission_service.get_user_permissions = AsyncMock(return_value={"*"})

    result = await permission_service.check_permissions(
        user_id=user_id,
        required_perms=["user:read", "order:write"],
        match="all",
        wildcard_support=True,
    )

    assert result is True


@pytest.mark.parametrize(
    "user_perms",
    [
        {"user:read", "user:write"},
        {"user:*"},
    ],
)
@pytest.mark.asyncio
async def test_check_permissions_module_without_action_as_wildcard(
    permission_service, user_perms
):
    user_id = 1
    permission_service.get_user_permissions = AsyncMock(return_value=user_perms)

    result = await permission_service.check_permissions(
        user_id=user_id, required_perms=["user"], match="all", wildcard_support=True
    )

    assert result is True


@pytest.mark.asyncio
async def test_check_roles_by_name(permission_service):
    user_id = 1
    permission_service.get_user_roles = AsyncMock(return_value={"admin", "user"})

    result = await permission_service.check_roles(
        user_id=user_id, required_roles=["admin"], match="all"
    )

    assert result is True
