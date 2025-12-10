from fastapi import Request
from fastapi.responses import JSONResponse

from src.exceptions import BusinessException
from src.responses.base import Response

from .interface import ExceptionHandler


BUSINESS_CODE_TO_HTTP_STATUS = {
    400: 400,
    401: 401,
    403: 403,
    404: 404,
    409: 409,
    418: 418,
    422: 422,
    500: 500,
}


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
        status_code = BUSINESS_CODE_TO_HTTP_STATUS.get(exc.business_code, 400)

        response = Response.error(
            code=exc.business_code,
            msg=exc.msg,
            data=exc.data
        )

        return JSONResponse(
            content=response.model_dump(),
            status_code=status_code
        )
