import uuid
from typing import Any

from fastapi import Depends, Request

from src.audit.service import AuditService, extract_client_info, get_audit_service
from src.core.schemas import User
from src.core.schemas.audit import AuditAction, AuditResult


async def generate_request_id(request: Request) -> str:
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    return request_id


async def audit_protected_access(
    request: Request,
    user: User,
    audit_service: AuditService = Depends(get_audit_service),
    request_id: str = Depends(generate_request_id),
) -> None:
    user_agent, ip = extract_client_info(request)

    extra: dict[str, Any] = {
        "method": request.method,
        "path": request.url.path,
    }
    if request.query_params:
        extra["query_params"] = dict(request.query_params)

    await audit_service.log(
        action=AuditAction.PROTECTED_RESOURCE_ACCESS,
        result=AuditResult.SUCCESS,
        actor_id=user.id,
        request_id=request_id,
        user_agent=user_agent,
        ip=ip,
        extra=extra,
    )
