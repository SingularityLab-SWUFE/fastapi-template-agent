from typing import Any, List

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.responses.base import Response

from .interface import ExceptionHandler


class ValidationExceptionHandler(ExceptionHandler):
    """Handler for Pydantic validation errors.

    Handles RequestValidationError raised when request data fails
    Pydantic validation.
    """

    def can_handle(self, exc: Exception) -> bool:
        """Check if the exception is a RequestValidationError.

        Args:
            exc: The exception to check

        Returns:
            True if the exception is a RequestValidationError
        """
        return isinstance(exc, RequestValidationError)

    async def handle(self, request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle RequestValidationError and return formatted validation errors.

        Args:
            request: The FastAPI request object
            exc: The RequestValidationError to handle

        Returns:
            JSONResponse with structured validation error details
        """
        errors = self._format_validation_errors(exc.errors())

        response = Response.error(
            code=422,
            msg="Validation failed",
            data={"validation_errors": errors}
        )

        return JSONResponse(
            content=response.model_dump(),
            status_code=422
        )

    @staticmethod
    def _format_validation_errors(errors: List[dict]) -> List[dict]:
        """Format Pydantic validation errors for client consumption.

        Args:
            errors: List of error dictionaries from Pydantic

        Returns:
            List of formatted error dictionaries with field, message, and type
        """
        formatted = []
        for error in errors:
            formatted.append({
                "field": ".".join(str(x) for x in error.get("loc", []) if x != "body"),
                "message": error.get("msg", ""),
                "type": error.get("type", "")
            })
        return formatted
