import logging
import uuid
from typing import Any

from starlette.types import ASGIApp, Receive, Scope, Send

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

        audit_ctx = AuditContext(
            trace_id=trace_id,
            request_id=request_id,
            method=scope.get("method", ""),
            path=scope.get("path", ""),
            query_params={},
            user_agent=user_agent or None,
            ip=ip,
        )

        async def send_wrapper(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                message["headers"].append((b"x-trace-id", trace_id.encode()))
                message["headers"].append((b"x-request-id", request_id.encode()))
            await send(message)

        scope["trace_id"] = trace_id
        scope["request_id"] = request_id
        scope["audit_ctx"] = audit_ctx

        await self.app(scope, receive, send_wrapper)


def get_audit_context(scope: Scope) -> AuditContext | None:
    return scope.get("audit_ctx")


def get_trace_id(scope: Scope) -> str | None:
    return scope.get("trace_id")
