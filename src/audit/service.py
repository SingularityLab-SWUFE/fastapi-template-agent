from typing import Any

from fastapi import Depends, Request
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit.schemas import AuditLog
from src.session import get_session


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_audit_log(
        self,
        action: str,
        result: str,
        actor_id: int | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        user_agent: str | None = None,
        ip: str | None = None,
        extra: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        audit_log = AuditLog(
            request_id=request_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result,
            user_agent=user_agent,
            ip=ip,
            extra=extra,
        )
        self.session.add(audit_log)
        await self.session.commit()


class AuditService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository

    async def log(
        self,
        action: str,
        result: str,
        actor_id: int | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        user_agent: str | None = None,
        ip: str | None = None,
        extra: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        try:
            await self.repository.create_audit_log(
                action=action,
                result=result,
                actor_id=actor_id,
                resource_type=resource_type,
                resource_id=resource_id,
                user_agent=user_agent,
                ip=ip,
                extra=extra,
                request_id=request_id,
            )
        except Exception:
            logger.exception("Failed to create audit log")


async def get_audit_service(
    session: AsyncSession = Depends(get_session),
) -> AuditService:
    repository = AuditRepository(session=session)
    return AuditService(repository=repository)


def extract_client_info(request: Request) -> tuple[str | None, str | None]:
    user_agent = request.headers.get("user-agent")
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else None
    return user_agent, ip
