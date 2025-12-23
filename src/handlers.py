import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from src.audit.middleware import get_trace_id
from src.core.schemas.audit import AuditAction, AuditResult
from src.core.schemas.error import error_code_to_http_status
from src.exceptions import BusinessException
from src.responses.base import Response

logger = logging.getLogger(__name__)

__all__ = ["register_exception_handlers"]


async def log_exception(
    request: Request,
    action: str,
    result: str,
    error_code: int,
    error_type: str,
    message: str,
    extra: dict[str, Any] | None = None,
) -> None:
    trace_id = get_trace_id(request.scope)
    request_id = request.scope.get("request_id")

    actor_id = None
    user = getattr(request.state, "user", None)
    if user is not None and hasattr(user, "id"):
        actor_id = user.id

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
                actor_id=actor_id,
                user_agent=request.headers.get("user-agent"),
                ip=request.client.host if request.client else None,
                extra={
                    "error_code": error_code,
                    "error_type": error_type,
                    "message": message,
                    "path": request.url.path,
                    "method": request.method,
                    **(extra or {}),
                },
            )
    except Exception:
        logger.exception("Failed to create audit log")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessException)
    async def handle_business_exception(
        request: Request, exc: BusinessException
    ) -> JSONResponse:
        http_status = error_code_to_http_status(exc.code)
        response = Response.error(code=int(exc.code), msg=exc.msg, data=exc.data)

        await log_exception(
            request,
            AuditAction.EXCEPTION,
            AuditResult.FAILURE,
            int(exc.code),
            exc.__class__.__name__,
            exc.msg,
            {"data": exc.data},
        )

        return JSONResponse(content=response.model_dump(), status_code=http_status)

    @app.exception_handler(HTTPException)
    async def handle_http_exception(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        if isinstance(exc.detail, str):
            detail = exc.detail
        elif isinstance(exc.detail, list) and exc.detail:
            detail = str(exc.detail[0])
        elif isinstance(exc.detail, dict):
            detail = exc.detail.get("msg", str(exc.detail))
        else:
            detail = str(exc.detail) if exc.detail is not None else "HTTP error"

        response = Response.error(code=exc.status_code, msg=detail, data=None)

        await log_exception(
            request,
            AuditAction.EXCEPTION,
            AuditResult.FAILURE,
            exc.status_code,
            exc.__class__.__name__,
            detail,
        )

        return JSONResponse(content=response.model_dump(), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {
                "field": ".".join(str(x) for x in e.get("loc", []) if x != "body"),
                "message": e.get("msg", ""),
                "type": e.get("type", ""),
            }
            for e in exc.errors()
        ]
        response = Response.error(
            code=422, msg="Validation failed", data={"validation_errors": errors}
        )

        await log_exception(
            request,
            AuditAction.EXCEPTION,
            AuditResult.FAILURE,
            422,
            exc.__class__.__name__,
            "Validation failed",
            {"validation_errors": errors},
        )

        return JSONResponse(content=response.model_dump(), status_code=422)

    @app.exception_handler(Exception)
    async def handle_fallback_exception(
        request: Request, exc: Exception
    ) -> JSONResponse:
        response = Response.error(
            code=500,
            msg="Internal server error",
            data={"error_type": exc.__class__.__name__},
        )

        await log_exception(
            request,
            AuditAction.EXCEPTION,
            AuditResult.FAILURE,
            500,
            exc.__class__.__name__,
            str(exc) or "Internal server error",
        )

        return JSONResponse(content=response.model_dump(), status_code=500)
