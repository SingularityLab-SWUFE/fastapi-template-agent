from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from src.exceptions import BusinessException, ErrorCode
from src.responses.base import Response

__all__ = ["register_exception_handlers"]

ERROR_CODE_TO_HTTP = {
    ErrorCode.AUTH_INVALID_CREDENTIALS: 401,
    ErrorCode.AUTH_INVALID_PASSWORD: 401,
    ErrorCode.AUTH_TOKEN_INVALID: 401,
    ErrorCode.AUTH_ACCOUNT_LOCKED: 403,
    ErrorCode.USER_NOT_FOUND: 404,
    ErrorCode.USER_INACTIVE: 403,
    ErrorCode.PERM_INSUFFICIENT: 403,
    ErrorCode.DATA_VALIDATION_FAILED: 422,
    ErrorCode.BIZ_INSUFFICIENT_BALANCE: 402,
    ErrorCode.BIZ_ORDER_EXPIRED: 410,
    ErrorCode.SYS_INTERNAL_ERROR: 500,
}


def _get_http_status(error_code: ErrorCode) -> int:
    return ERROR_CODE_TO_HTTP.get(error_code, 400)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessException)
    async def handle_business_exception(
        request: Request, exc: BusinessException
    ) -> JSONResponse:
        http_status = _get_http_status(exc.code)
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
