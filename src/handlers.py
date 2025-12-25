import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from src.exceptions import BusinessException
from src.responses.base import Response
from src.shared.errors import error_code_to_http_status

logger = logging.getLogger(__name__)

__all__ = ["register_exception_handlers"]


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessException)
    async def handle_business_exception(
        request: Request, exc: BusinessException
    ) -> JSONResponse:
        http_status = error_code_to_http_status(exc.code)
        response = Response.error(code=int(exc.code), msg=exc.msg, data=exc.data)
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
        return JSONResponse(content=response.model_dump(), status_code=500)
