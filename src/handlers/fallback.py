import logging
import traceback

from fastapi import Request
from fastapi.responses import JSONResponse

from src.responses.base import Response

from .interface import ExceptionHandler


logger = logging.getLogger(__name__)


class FallbackExceptionHandler(ExceptionHandler):
    """Fallback handler for unhandled exceptions.

    This handler catches any exception that wasn't handled by previous
    handlers in the chain. It logs the exception for monitoring and
    returns a generic internal server error response.
    """

    def can_handle(self, exc: Exception) -> bool:
        """This handler can handle ANY exception.

        Should be last in the chain as a catch-all.

        Args:
            exc: The exception to check

        Returns:
            Always True
        """
        return True

    async def handle(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle unhandled exception with logging and generic error response.

        Args:
            request: The FastAPI request object
            exc: The unhandled exception

        Returns:
            JSONResponse with generic 500 error
        """
        logger.error(
            "Unhandled exception in request %s %s: %s",
            request.method,
            request.url.path,
            exc,
            exc_info=True
        )

        response = Response.error(
            code=500,
            msg="Internal server error",
            data={
                "error_type": exc.__class__.__name__,
                "error_id": id(exc)
            }
        )

        return JSONResponse(
            content=response.model_dump(),
            status_code=500
        )
