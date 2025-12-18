import pytest
from unittest.mock import AsyncMock, MagicMock

from src.auth.rbac import PermissionRepository, PermissionService


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def permission_service(mock_session):
    repository = PermissionRepository(mock_session)
    return PermissionService(repository=repository)


@pytest.mark.asyncio
async def test_get_user_permissions(mock_session, permission_service):
    user_id = 1
    mock_session.execute.return_value.scalars = MagicMock(
        return_value=MagicMock(all=MagicMock(return_value=["user:read", "user:write"]))
    )

    result = await permission_service.repository.get_user_permissions(user_id)

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
    permission_service.repository.get_user_permissions = AsyncMock(
        return_value=user_perms
    )

    result = await permission_service.check_permissions(
        user_id=user_id, required_perms=required_perms, match=match
    )

    assert result is expected


@pytest.mark.asyncio
async def test_check_permissions_invalid_match_raises(permission_service):
    permission_service.repository.get_user_permissions = AsyncMock(
        return_value={"user:read"}
    )

    with pytest.raises(ValueError, match="match must be 'all' or 'any'"):
        await permission_service.check_permissions(
            user_id=1,
            required_perms=["user:read", "user:write"],
            match="ALL",  # type: ignore[arg-type]
        )


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
    permission_service.repository.get_user_permissions = AsyncMock(
        return_value=user_perms
    )

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
        ({"user:read"}, [""], True, False),
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
    permission_service.repository.get_user_permissions = AsyncMock(
        return_value=user_perms
    )

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
    permission_service.repository.get_user_permissions = AsyncMock(return_value={"*"})

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
    permission_service.repository.get_user_permissions = AsyncMock(
        return_value=user_perms
    )

    result = await permission_service.check_permissions(
        user_id=user_id, required_perms=["user"], match="all", wildcard_support=True
    )

    assert result is False


@pytest.mark.asyncio
async def test_check_roles_by_name(permission_service):
    user_id = 1
    permission_service.repository.get_user_roles = AsyncMock(
        return_value={"admin", "user"}
    )

    result = await permission_service.check_roles(
        user_id=user_id, required_roles=["admin"], match="all"
    )

    assert result is True


@pytest.mark.asyncio
async def test_check_roles_invalid_match_raises(permission_service):
    permission_service.repository.get_user_roles = AsyncMock(return_value={"admin"})

    with pytest.raises(ValueError, match="match must be 'all' or 'any'"):
        await permission_service.check_roles(
            user_id=1,
            required_roles=["admin", "moderator"],
            match="ALL",  # type: ignore[arg-type]
        )


@pytest.mark.asyncio
async def test_get_user_roles(mock_session, permission_service):
    user_id = 1
    mock_session.execute.return_value.scalars = MagicMock(
        return_value=MagicMock(all=MagicMock(return_value=["admin", "user"]))
    )

    result = await permission_service.repository.get_user_roles(user_id)

    assert result == {"admin", "user"}


@pytest.mark.parametrize(
    "user_perms,required_perms,match,expected",
    [
        ({"user:read"}, ["admin:write"], "all", False),
        ({"user:read"}, ["user:read", "user:write"], "all", False),
        ({"user:read"}, ["user:read", "user:write"], "any", True),
    ],
)
@pytest.mark.asyncio
async def test_check_permissions_with_various_scenarios(
    user_perms, required_perms, match, expected
):
    service = PermissionService(repository=AsyncMock())
    service.repository.get_user_permissions = AsyncMock(return_value=user_perms)

    result = await service.check_permissions(
        user_id=1, required_perms=required_perms, match=match
    )

    assert result is expected


@pytest.mark.parametrize(
    "user_roles,required_roles,match,expected",
    [
        ({"user"}, ["admin"], "all", False),
        ({"user"}, ["user", "admin"], "all", False),
        ({"user"}, ["user", "admin"], "any", True),
        (set(), [], "all", True),
    ],
)
@pytest.mark.asyncio
async def test_check_roles_with_various_scenarios(
    user_roles, required_roles, match, expected
):
    service = PermissionService(repository=AsyncMock())
    service.repository.get_user_roles = AsyncMock(return_value=user_roles)

    result = await service.check_roles(
        user_id=1, required_roles=required_roles, match=match
    )

    assert result is expected


@pytest.mark.parametrize(
    "required_perm,user_perm,wildcard_support,expected",
    [
        ("user:read", "user:read", False, True),
        ("user:read", "user:*", False, False),
        ("user:*", "user:read", False, False),
        ("*", "*", True, True),
        ("*", "user:read", True, False),
        ("user:read", "*", True, True),
        ("admin:write", "*", True, True),
        ("user:read", "admin:read", True, False),
        ("user", "user:read", True, False),
        ("user", "user:write", True, False),
        ("user:read", "user", True, True),
        ("user:write", "user", True, True),
        ("user:read", "user:*", True, True),
        ("user:write", "user:*", True, True),
    ],
)
@pytest.mark.asyncio
async def test_match_permission_scenarios(
    required_perm, user_perm, wildcard_support, expected
):
    service = PermissionService(repository=AsyncMock())

    result = service._match_permission(required_perm, user_perm, wildcard_support)

    assert result is expected


@pytest.mark.parametrize(
    "permission,expected_module,expected_action",
    [
        ("user:read", "user", "read"),
        ("user", "user", None),
        ("user:", "user", None),
        ("admin:write:extra", "admin", "write:extra"),
    ],
)
@pytest.mark.asyncio
async def test_split_permission_scenarios(permission, expected_module, expected_action):
    service = PermissionService(repository=AsyncMock())

    module, action = service._split_permission(permission)

    assert module == expected_module
    assert action == expected_action
