from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .exceptions import BusinessException


def register_business_exception_handler(app: FastAPI) -> None:
    """
    Attach handler converting BusinessException to HTTP responses.

    Args:
        app: FastAPI application where the handler is registered.
    """

    @app.exception_handler(BusinessException)
    async def business_exception_handler(_request: Request, exc: BusinessException) -> JSONResponse:
        status_code = exc.code if 100 <= exc.code < 600 else 400
        payload = {
            "code": exc.code,
            "msg": exc.msg,
            "detail": exc.msg,
        }
        return JSONResponse(status_code=status_code, content=payload)
