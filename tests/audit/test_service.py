import pytest
from unittest.mock import AsyncMock, MagicMock

from src.audit.service import AuditRepository, AuditService
from src.audit.schemas import AuditAction, AuditResult


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def audit_repository(mock_session):
    return AuditRepository(mock_session)


@pytest.fixture
def audit_service(audit_repository):
    return AuditService(repository=audit_repository)


@pytest.mark.asyncio
async def test_create_audit_log(audit_repository, mock_session):
    await audit_repository.create_audit_log(
        action=AuditAction.LOGIN,
        result=AuditResult.SUCCESS,
        actor_id=1,
        user_agent="test-agent",
        ip="127.0.0.1",
        extra={"key": "value"},
    )

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_log_success(audit_service, mock_session):
    await audit_service.log(
        action=AuditAction.LOGIN,
        result=AuditResult.SUCCESS,
        actor_id=1,
        user_agent="test-agent",
        ip="127.0.0.1",
    )

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_log_handles_exception(audit_service, mock_session):
    mock_session.commit.side_effect = Exception("DB error")

    await audit_service.log(
        action=AuditAction.LOGIN,
        result=AuditResult.FAILURE,
        actor_id=1,
    )
