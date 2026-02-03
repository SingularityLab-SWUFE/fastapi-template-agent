import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.service import AuthenticationService
from src.auth.schemas import TokenResponse
from src.audit.schemas import AuditAction, AuditResult
from src.shared.errors import ErrorCode
from src.exceptions import BusinessException


@pytest.fixture
def mock_user_manager():
    manager = AsyncMock()
    return manager


@pytest.fixture
def mock_jwt_strategy():
    strategy = AsyncMock()
    return strategy


@pytest.fixture
def mock_refresh_manager():
    manager = AsyncMock()
    return manager


@pytest.fixture
def mock_audit_service():
    service = AsyncMock()
    return service


@pytest.fixture
def mock_request():
    request = MagicMock(spec=Request)
    request.headers = {"user-agent": "test-agent"}
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    return request


@pytest.fixture
def auth_service(
    mock_user_manager, mock_jwt_strategy, mock_refresh_manager, mock_audit_service
):
    return AuthenticationService(
        user_manager=mock_user_manager,
        strategy=mock_jwt_strategy,
        refresh_manager=mock_refresh_manager,
        audit_service=mock_audit_service,
    )


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.is_active = True
    return user


@pytest.fixture
def mock_credentials():
    credentials = MagicMock(spec=OAuth2PasswordRequestForm)
    credentials.username = "testuser"
    credentials.password = "testpass"
    return credentials


@pytest.mark.asyncio
async def test_login_success(
    auth_service,
    mock_user_manager,
    mock_jwt_strategy,
    mock_refresh_manager,
    mock_audit_service,
    mock_request,
    mock_credentials,
    mock_user,
):
    mock_user_manager.authenticate.return_value = mock_user
    mock_jwt_strategy.write_token.return_value = "access_token_123"
    mock_refresh_manager.create_refresh_token.return_value = "refresh_token_123"

    result = await auth_service.login(mock_credentials, mock_request)

    assert isinstance(result, TokenResponse)
    assert result.access_token == "access_token_123"
    assert result.refresh_token == "refresh_token_123"
    assert result.token_type == "Bearer"

    mock_user_manager.authenticate.assert_called_once_with(mock_credentials)
    mock_jwt_strategy.write_token.assert_called_once_with(mock_user)
    mock_refresh_manager.create_refresh_token.assert_called_once_with(1, "test-agent")

    assert mock_audit_service.log.call_count == 1
    call_args = mock_audit_service.log.call_args.kwargs
    assert call_args["action"] == AuditAction.LOGIN
    assert call_args["result"] == AuditResult.SUCCESS
    assert call_args["actor_id"] == 1


@pytest.mark.asyncio
async def test_login_invalid_credentials(
    auth_service,
    mock_user_manager,
    mock_audit_service,
    mock_request,
    mock_credentials,
):
    mock_user_manager.authenticate.return_value = None

    with pytest.raises(BusinessException) as exc_info:
        await auth_service.login(mock_credentials, mock_request)

    assert exc_info.value.code == ErrorCode.AUTH_INVALID_CREDENTIALS

    assert mock_audit_service.log.call_count == 1
    call_args = mock_audit_service.log.call_args.kwargs
    assert call_args["action"] == AuditAction.LOGIN
    assert call_args["result"] == AuditResult.FAILURE
    assert call_args["extra"]["username"] == "testuser"


@pytest.mark.asyncio
async def test_login_inactive_user(
    auth_service,
    mock_user_manager,
    mock_audit_service,
    mock_request,
    mock_credentials,
    mock_user,
):
    mock_user.is_active = False
    mock_user_manager.authenticate.return_value = mock_user

    with pytest.raises(BusinessException) as exc_info:
        await auth_service.login(mock_credentials, mock_request)

    assert exc_info.value.code == ErrorCode.AUTH_INVALID_CREDENTIALS

    assert mock_audit_service.log.call_count == 1
    call_args = mock_audit_service.log.call_args.kwargs
    assert call_args["action"] == AuditAction.LOGIN
    assert call_args["result"] == AuditResult.FAILURE


@pytest.mark.asyncio
async def test_refresh_success(
    auth_service,
    mock_user_manager,
    mock_jwt_strategy,
    mock_refresh_manager,
    mock_audit_service,
    mock_request,
    mock_user,
):
    mock_refresh_manager.verify_refresh_token.return_value = 1
    mock_user_manager.get.return_value = mock_user
    mock_jwt_strategy.write_token.return_value = "new_access_token"
    mock_refresh_manager.create_refresh_token.return_value = "new_refresh_token"

    result = await auth_service.refresh("old_refresh_token", mock_request)

    assert isinstance(result, TokenResponse)
    assert result.access_token == "new_access_token"
    assert result.refresh_token == "new_refresh_token"

    mock_refresh_manager.verify_refresh_token.assert_called_once_with(
        "old_refresh_token"
    )
    mock_user_manager.get.assert_called_once_with(1)
    mock_jwt_strategy.write_token.assert_called_once_with(mock_user)
    mock_refresh_manager.revoke_token.assert_called_once_with("old_refresh_token")

    assert mock_audit_service.log.call_count == 1
    call_args = mock_audit_service.log.call_args.kwargs
    assert call_args["action"] == AuditAction.REFRESH
    assert call_args["result"] == AuditResult.SUCCESS


@pytest.mark.asyncio
async def test_refresh_invalid_token(
    auth_service,
    mock_refresh_manager,
    mock_audit_service,
    mock_request,
):
    mock_refresh_manager.verify_refresh_token.return_value = None

    with pytest.raises(BusinessException) as exc_info:
        await auth_service.refresh("invalid_token", mock_request)

    assert exc_info.value.code == ErrorCode.AUTH_TOKEN_INVALID

    assert mock_audit_service.log.call_count == 1
    call_args = mock_audit_service.log.call_args.kwargs
    assert call_args["action"] == AuditAction.REFRESH
    assert call_args["result"] == AuditResult.FAILURE


@pytest.mark.asyncio
async def test_refresh_inactive_user(
    auth_service,
    mock_user_manager,
    mock_refresh_manager,
    mock_audit_service,
    mock_request,
    mock_user,
):
    mock_refresh_manager.verify_refresh_token.return_value = 1
    mock_user.is_active = False
    mock_user_manager.get.return_value = mock_user

    with pytest.raises(BusinessException) as exc_info:
        await auth_service.refresh("valid_token", mock_request)

    assert exc_info.value.code == ErrorCode.USER_INACTIVE

    assert mock_audit_service.log.call_count == 1
    call_args = mock_audit_service.log.call_args.kwargs
    assert call_args["action"] == AuditAction.REFRESH
    assert call_args["result"] == AuditResult.FAILURE
    assert call_args["actor_id"] == 1


@pytest.mark.asyncio
async def test_refresh_user_not_found(
    auth_service,
    mock_user_manager,
    mock_refresh_manager,
    mock_audit_service,
    mock_request,
):
    mock_refresh_manager.verify_refresh_token.return_value = 1
    mock_user_manager.get.return_value = None

    with pytest.raises(BusinessException) as exc_info:
        await auth_service.refresh("valid_token", mock_request)

    assert exc_info.value.code == ErrorCode.USER_INACTIVE


@pytest.mark.asyncio
async def test_logout_success(
    auth_service,
    mock_refresh_manager,
    mock_audit_service,
    mock_request,
):
    mock_refresh_manager.verify_refresh_token.return_value = 1

    result = await auth_service.logout("refresh_token", mock_request)

    assert result is None

    mock_refresh_manager.verify_refresh_token.assert_called_once_with("refresh_token")
    mock_refresh_manager.revoke_token.assert_called_once_with("refresh_token")

    assert mock_audit_service.log.call_count == 1
    call_args = mock_audit_service.log.call_args.kwargs
    assert call_args["action"] == AuditAction.LOGOUT
    assert call_args["result"] == AuditResult.SUCCESS
    assert call_args["actor_id"] == 1


@pytest.mark.asyncio
async def test_logout_invalid_token(
    auth_service,
    mock_refresh_manager,
    mock_audit_service,
    mock_request,
):
    mock_refresh_manager.verify_refresh_token.return_value = None

    with pytest.raises(BusinessException) as exc_info:
        await auth_service.logout("invalid_token", mock_request)

    assert exc_info.value.code == ErrorCode.AUTH_TOKEN_INVALID

    assert mock_audit_service.log.call_count == 1
    call_args = mock_audit_service.log.call_args.kwargs
    assert call_args["action"] == AuditAction.LOGOUT
    assert call_args["result"] == AuditResult.FAILURE
