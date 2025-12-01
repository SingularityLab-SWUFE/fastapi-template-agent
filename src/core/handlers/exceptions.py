from abc import ABC, abstractmethod
from typing import Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

class BaseExceptionHandler(ABC):
    def __init__(self, next_handler: Optional["BaseExceptionHandler"] = None):
        self._next_handler = next_handler

    async def handle(self, request: Request, exc: Exception) -> JSONResponse:
        if await self.can_handle(exc):
            return await self.process(request, exc)

        if self._next_handler:
            return await self._next_handler.handle(request, exc)

        return await self._default_handle(request, exc)

    @abstractmethod
    async def can_handle(self, exc: Exception) -> bool:
        pass

    @abstractmethod
    async def process(self, request: Request, exc: Exception) -> JSONResponse:
        pass

    async def _default_handle(self, request: Request, exc: Exception) -> JSONResponse:
        from src.core.responses.schemas import ErrorResponse
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse.error(
                code=HTTP_500_INTERNAL_SERVER_ERROR,
                msg=str(exc)
            ).model_dump()
        )

class HTTPExceptionHandler(BaseExceptionHandler):
    async def can_handle(self, exc: Exception) -> bool:
        return isinstance(exc, HTTPException)

    async def process(self, request: Request, exc: HTTPException) -> JSONResponse:
        from src.core.responses.schemas import ErrorResponse
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse.error(
                code=exc.status_code,
                msg=exc.detail
            ).model_dump()
        )

class ValueErrorHandler(BaseExceptionHandler):
    async def can_handle(self, exc: Exception) -> bool:
        return isinstance(exc, ValueError)

    async def process(self, request: Request, exc: ValueError) -> JSONResponse:
        from src.core.responses.schemas import ErrorResponse
        return JSONResponse(
            status_code=400,
            content=ErrorResponse.error(
                code=400,
                msg=str(exc)
            ).model_dump()
        )

class BusinessException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(self.message)

class BusinessExceptionHandler(BaseExceptionHandler):
    async def can_handle(self, exc: Exception) -> bool:
        return isinstance(exc, BusinessException)

    async def process(self, request: Request, exc: BusinessException) -> JSONResponse:
        from src.core.responses.schemas import ErrorResponse
        return JSONResponse(
            status_code=200,
            content=ErrorResponse.error(
                code=exc.code,
                msg=exc.message
            ).model_dump()
        )
