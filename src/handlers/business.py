from fastapi import Request
from fastapi.responses import JSONResponse

from src.exceptions import BusinessException
from src.responses.base import Response

from .interface import ExceptionHandler


class BusinessExceptionHandler(ExceptionHandler):
    """Handler for BusinessException with domain-specific error codes.

    Handles application-specific business logic exceptions that carry
    custom error codes and messages.
    """

    def can_handle(self, exc: Exception) -> bool:
        """Check if the exception is a BusinessException.

        Args:
            exc: The exception to check

        Returns:
            True if the exception is a BusinessException
        """
        return isinstance(exc, BusinessException)

    async def handle(self, request: Request, exc: BusinessException) -> JSONResponse:
        """Handle BusinessException and return a unified error response.

        Args:
            request: The FastAPI request object
            exc: The BusinessException to handle

        Returns:
            JSONResponse with the exception's code and message
        """
        # Validate HTTP status code is within valid range
        status_code = exc.http_code if 100 <= exc.http_code < 600 else 400

        response = Response.error(
            code=exc.business_code,
            msg=exc.msg,
            data=None
        )

        return JSONResponse(
            content=response.model_dump(),
            status_code=status_code
        )
