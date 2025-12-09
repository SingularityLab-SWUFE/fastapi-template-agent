from __future__ import annotations

import logging
from typing import Iterable

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from src.exceptions import BusinessException

from .business import BusinessExceptionHandler
from .fallback import FallbackExceptionHandler
from .http import HTTPExceptionHandler
from .interface import ExceptionHandler
from .validation import ValidationExceptionHandler

__all__ = [
    "build_exception_chain",
    "register_exception_handlers",
    "ExceptionHandler",
]


logger = logging.getLogger(__name__)


def build_exception_chain(handlers: Iterable[ExceptionHandler]) -> ExceptionHandler:
    """Build a chained exception handler from individual handlers.

    The chain processes exceptions in order, using the first handler
    that can handle the exception type. If a handler raises an exception
    during processing, the chain continues to the next handler.

    Args:
        handlers: Iterable of handlers in priority order

    Returns:
        A composite handler that delegates to the chain
    """
    handler_list = list(handlers)

    async def chain_handler(request: Request, exc: Exception) -> JSONResponse:
        """Process exception through the handler chain.

        Args:
            request: The FastAPI request object
            exc: The exception to handle

        Returns:
            JSONResponse from the first matching handler
        """
        for handler in handler_list:
            try:
                if handler.can_handle(exc):
                    logger.debug(
                        "Handler %s handling exception %s",
                        handler.__class__.__name__,
                        exc.__class__.__name__
                    )
                    return await handler.handle(request, exc)
            except Exception as e:
                logger.error(
                    "Error in handler %s: %s",
                    handler.__class__.__name__,
                    e,
                    exc_info=True
                )
                continue

        logger.warning(
            "No handler found for exception %s, using fallback",
            exc.__class__.__name__
        )
        fallback = FallbackExceptionHandler()
        return await fallback.handle(request, exc)

    return chain_handler


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app.

    This function registers individual exception handlers for specific
    exception types, allowing the handler chain to process them in order.

    Args:
        app: FastAPI application instance
    """
    handlers = [
        BusinessExceptionHandler(),
        HTTPExceptionHandler(),
        ValidationExceptionHandler(),
        FallbackExceptionHandler(),
    ]

    chain = build_exception_chain(handlers)

    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
        return await chain(request, exc)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return await chain(request, exc)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return await chain(request, exc)

    @app.exception_handler(Exception)
    async def fallback_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return await chain(request, exc)

    logger.info("Registered exception handler chain")
