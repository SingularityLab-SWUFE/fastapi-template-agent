import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .service import extract_client_info


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


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        trace_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())

        user_agent, ip = extract_client_info(request)

        audit_ctx = AuditContext(
            trace_id=trace_id,
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            user_agent=user_agent,
            ip=ip,
        )

        request.state.trace_id = trace_id
        request.state.request_id = request_id
        request.state.audit_ctx = audit_ctx

        response = await call_next(request)

        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Request-ID"] = request_id

        return response


def get_audit_context(request: Request) -> AuditContext | None:
    return getattr(request.state, "audit_ctx", None)


def get_trace_id(request: Request) -> str | None:
    return getattr(request.state, "trace_id", None)
