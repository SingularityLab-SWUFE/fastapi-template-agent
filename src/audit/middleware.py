import logging
import uuid
from typing import Any
from urllib.parse import parse_qsl

from starlette.types import ASGIApp, Receive, Scope, Send

from src.core.schemas.audit import AuditAction, AuditResult

logger = logging.getLogger(__name__)


class AuditContext:
    def __init__(
        self,
        trace_id: str,
        request_id: str,
        method: str,
        path: str,
        query_params: dict,
        user_agent: str | None,
        ip: str | None,
    ):
        self.trace_id = trace_id
        self.request_id = request_id
        self.method = method
        self.path = path
        self.query_params = query_params
        self.user_agent = user_agent
        self.ip = ip


class AuditMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        trace_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())

        request_headers = dict(scope.get("headers", []))
        user_agent = request_headers.get(b"user-agent", b"").decode()
        forwarded_for = request_headers.get(b"x-forwarded-for", b"").decode()
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
        else:
            client = scope.get("client")
            ip = client[0] if client else None

        query_string = scope.get("query_string", b"").decode()
        query_params = dict(parse_qsl(query_string, keep_blank_values=True))

        audit_ctx = AuditContext(
            trace_id=trace_id,
            request_id=request_id,
            method=scope.get("method", ""),
            path=scope.get("path", ""),
            query_params=query_params,
            user_agent=user_agent or None,
            ip=ip,
        )

        async def log_event(
            action: str, result: str, extra: dict[str, Any] | None = None
        ) -> None:
            try:
                from src.session import async_session_factory

                from src.audit.service import AuditRepository, AuditService

                async with async_session_factory() as session:
                    repository = AuditRepository(session)
                    service = AuditService(repository)
                    await service.log(
                        action=action,
                        result=result,
                        trace_id=trace_id,
                        request_id=request_id,
                        user_agent=audit_ctx.user_agent,
                        ip=audit_ctx.ip,
                        extra={
                            "path": audit_ctx.path,
                            "method": audit_ctx.method,
                            "query_params": audit_ctx.query_params,
                            **(extra or {}),
                        },
                    )
            except Exception:
                logger.exception("Failed to create audit log")

        status_code: int | None = None

        async def send_wrapper(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status")
                message["headers"].append((b"x-trace-id", trace_id.encode()))
                message["headers"].append((b"x-request-id", request_id.encode()))
            await send(message)

        scope["trace_id"] = trace_id
        scope["request_id"] = request_id
        scope["audit_ctx"] = audit_ctx

        await log_event(AuditAction.REQUEST_RECEIVED, AuditResult.SUCCESS)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            await log_event(
                AuditAction.RESPONSE_SENT,
                AuditResult.SUCCESS,
                {"status_code": status_code},
            )


def get_audit_context(scope: Scope) -> AuditContext | None:
    return scope.get("audit_ctx")


def get_trace_id(scope: Scope) -> str | None:
    return scope.get("trace_id")
