import pytest
from unittest.mock import AsyncMock, MagicMock

from src.auth.permission_service import PermissionService
from src.auth.rbac import RBACDependencies
from src.exceptions import InsufficientPermissionException, InsufficientRoleException


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def permission_service(mock_session):
    return PermissionService(mock_session)


@pytest.fixture
def rbac_deps(permission_service):
    return RBACDependencies(permission_service)


@pytest.mark.asyncio
async def test_get_user_permissions(mock_session, permission_service):
    user_id = 1
    mock_session.execute.return_value.scalars = MagicMock(
        return_value=MagicMock(all=MagicMock(return_value=["user:read", "user:write"]))
    )

    result = await permission_service.get_user_permissions(user_id)

    assert result == {"user:read", "user:write"}


@pytest.mark.asyncio
async def test_check_permissions_all_match(permission_service):
    user_id = 1
    permission_service.get_user_permissions = AsyncMock(
        return_value={"user:read", "user:write"}
    )

    result = await permission_service.check_permissions(
        user_id=user_id, required_perms=["user:read", "user:write"], match="all"
    )

    assert result is True


@pytest.mark.asyncio
async def test_check_permissions_any_match(permission_service):
    user_id = 1
    permission_service.get_user_permissions = AsyncMock(return_value={"user:read"})

    result = await permission_service.check_permissions(
        user_id=user_id, required_perms=["user:read", "user:write"], match="any"
    )

    assert result is True


@pytest.mark.asyncio
async def test_check_permissions_wildcard_match(permission_service):
    user_id = 1
    permission_service.get_user_permissions = AsyncMock(
        return_value={"user:read", "user:write"}
    )

    result = await permission_service.check_permissions(
        user_id=user_id, required_perms=["user:*"], match="all", wildcard_support=True
    )

    assert result is True


@pytest.mark.asyncio
async def test_check_permissions_module_wildcard_from_user(permission_service):
    user_id = 1
    permission_service.get_user_permissions = AsyncMock(return_value={"user:*"})

    result = await permission_service.check_permissions(
        user_id=user_id,
        required_perms=["user:read"],
        match="all",
        wildcard_support=True,
    )

    assert result is True


@pytest.mark.asyncio
async def test_check_permissions_trailing_colon_not_module_wildcard(permission_service):
    user_id = 1
    permission_service.get_user_permissions = AsyncMock(
        return_value={"user:read", "user:*"}
    )

    result = await permission_service.check_permissions(
        user_id=user_id,
        required_perms=["user:"],
        match="all",
        wildcard_support=True,
    )

    assert result is False


@pytest.mark.asyncio
async def test_check_permissions_trailing_colon_without_wildcard_support(
    permission_service,
):
    user_id = 1
    permission_service.get_user_permissions = AsyncMock(return_value={"user:read"})

    result = await permission_service.check_permissions(
        user_id=user_id,
        required_perms=["user:"],
        match="all",
        wildcard_support=False,
    )

    assert result is False


@pytest.mark.asyncio
async def test_check_permissions_empty_required_as_wildcard(permission_service):
    user_id = 1
    permission_service.get_user_permissions = AsyncMock(return_value={"user:read"})

    result = await permission_service.check_permissions(
        user_id=user_id,
        required_perms=[""],
        match="all",
        wildcard_support=True,
    )

    assert result is True


@pytest.mark.asyncio
async def test_check_permissions_empty_required_without_wildcard_support(
    permission_service,
):
    user_id = 1
    permission_service.get_user_permissions = AsyncMock(return_value={"user:read"})

    result = await permission_service.check_permissions(
        user_id=user_id,
        required_perms=[""],
        match="all",
        wildcard_support=False,
    )

    assert result is False


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


@pytest.mark.asyncio
async def test_check_roles_by_name(permission_service):
    user_id = 1
    permission_service.get_user_roles = AsyncMock(return_value={"admin", "user"})

    result = await permission_service.check_roles(
        user_id=user_id, required_roles=["admin"], match="all"
    )

    assert result is True


@pytest.mark.asyncio
async def test_require_permissions_dependency(rbac_deps):
    user = MagicMock()
    user.id = 1
    user.is_superuser = False
    rbac_deps.permission_service.check_permissions = AsyncMock(return_value=True)

    dependency = rbac_deps.require_permissions("user:read")
    result = await dependency(user=user)

    assert result is None


@pytest.mark.asyncio
async def test_require_permissions_insufficient(rbac_deps):
    user = MagicMock()
    user.id = 1
    user.is_superuser = False
    rbac_deps.permission_service.check_permissions = AsyncMock(return_value=False)
    rbac_deps.permission_service.get_user_permissions = AsyncMock(return_value=set())

    dependency = rbac_deps.require_permissions("user:read")

    with pytest.raises(InsufficientPermissionException) as exc:
        await dependency(user=user)

    assert exc.value.code == 30001


@pytest.mark.asyncio
async def test_require_roles_dependency(rbac_deps):
    user = MagicMock()
    user.id = 1
    user.is_superuser = False
    rbac_deps.permission_service.check_roles = AsyncMock(return_value=True)

    dependency = rbac_deps.require_roles("admin")
    result = await dependency(user=user)

    assert result is None


@pytest.mark.asyncio
async def test_require_roles_insufficient(rbac_deps):
    user = MagicMock()
    user.id = 1
    user.is_superuser = False
    rbac_deps.permission_service.check_roles = AsyncMock(return_value=False)
    rbac_deps.permission_service.get_user_roles = AsyncMock(return_value={"viewer"})

    dependency = rbac_deps.require_roles("admin")

    with pytest.raises(InsufficientRoleException) as exc:
        await dependency(user=user)

    assert exc.value.code == 30001
    assert "admin" in exc.value.data["required"]
    assert "viewer" in exc.value.data["user_roles"]


@pytest.mark.asyncio
async def test_owner_or_perm_owner_access(rbac_deps):
    user = MagicMock()
    user.id = 1
    user.is_superuser = False
    rbac_deps.permission_service.check_permissions = AsyncMock()

    dependency = rbac_deps.owner_or_perm(owner_id=1, perms="user:read")
    result = await dependency(user=user)

    assert result is None
    rbac_deps.permission_service.check_permissions.assert_not_called()


@pytest.mark.asyncio
async def test_owner_or_perm_permission_access(rbac_deps):
    user = MagicMock()
    user.id = 2
    user.is_superuser = False
    rbac_deps.permission_service.check_permissions = AsyncMock(return_value=True)

    dependency = rbac_deps.owner_or_perm(owner_id=1, perms="user:read")
    result = await dependency(user=user)

    assert result is None
    rbac_deps.permission_service.check_permissions.assert_called_once()


@pytest.mark.asyncio
async def test_owner_or_perm_permission_denied(rbac_deps):
    user = MagicMock()
    user.id = 2
    user.is_superuser = False
    rbac_deps.permission_service.check_permissions = AsyncMock(return_value=False)
    rbac_deps.permission_service.get_user_permissions = AsyncMock(return_value=set())

    dependency = rbac_deps.owner_or_perm(owner_id=1, perms=["user:read"])

    with pytest.raises(InsufficientPermissionException) as exc:
        await dependency(user=user)

    assert exc.value.code == 30001
