from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from src.core.handlers.exceptions import (
    HTTPExceptionHandler,
    ValueErrorHandler,
    BusinessExceptionHandler,
)

class ExceptionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.exception_handler = HTTPExceptionHandler(
            ValueErrorHandler(
                BusinessExceptionHandler()
            )
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self.exception_handler.handle(request, exc)
