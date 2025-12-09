from typing import Protocol, runtime_checkable

from fastapi import Request
from fastapi.responses import JSONResponse


@runtime_checkable
class ExceptionHandler(Protocol):
    """Protocol for exception handlers in the chain.

    Each handler in the chain should implement this protocol to handle
    specific types of exceptions.
    """

    def can_handle(self, exc: Exception) -> bool:
        """Check if this handler can process the exception.

        Args:
            exc: The exception to check

        Returns:
            True if this handler can process the exception
        """
        ...

    async def handle(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle the exception and return a JSON response.

        Args:
            request: The FastAPI request object
            exc: The exception to handle

        Returns:
            JSONResponse with unified error format
        """
        ...
