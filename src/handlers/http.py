from http import HTTPStatus
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

from src.responses.base import Response

from .interface import ExceptionHandler


class HTTPExceptionHandler(ExceptionHandler):
    """Handler for FastAPI HTTPException.

    Handles standard HTTP errors raised by FastAPI or manually raised
    in route handlers.
    """

    def can_handle(self, exc: Exception) -> bool:
        """Check if the exception is an HTTPException.

        Args:
            exc: The exception to check

        Returns:
            True if the exception is an HTTPException
        """
        return isinstance(exc, HTTPException)

    async def handle(self, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTPException and return a unified error response.

        Args:
            request: The FastAPI request object
            exc: The HTTPException to handle

        Returns:
            JSONResponse with the exception's status code and detail
        """
        detail = self._extract_detail(exc.status_code, exc.detail)

        response = Response.error(
            code=exc.status_code,
            msg=detail,
            data=None
        )

        return JSONResponse(
            content=response.model_dump(),
            status_code=exc.status_code
        )

    @staticmethod
    def _extract_detail(status_code: int, detail: Any) -> str:
        """Extract string message from various detail formats.

        Args:
            status_code: HTTP status code associated with the exception
            detail: The detail field from HTTPException (can be str, list, dict, etc.)

        Returns:
            A string representation of the detail
        """
        if isinstance(detail, str):
            return detail
        if isinstance(detail, list) and detail:
            return str(detail[0])
        if isinstance(detail, dict):
            return detail.get("msg", str(detail))
        try:
            return HTTPStatus(status_code).phrase
        except ValueError:
            return "HTTP error"
