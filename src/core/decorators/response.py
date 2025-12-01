from functools import wraps
from typing import Callable, TypeVar, Awaitable
from fastapi import Request
from src.core.responses.schemas import SuccessResponse, PaginatedResponse, PaginationInfo

T = TypeVar('T')

def handle_response(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[dict]]:
    @wraps(func)
    async def wrapper(*args, **kwargs) -> dict:
        try:
            result = await func(*args, **kwargs)
            return SuccessResponse.success(result).model_dump()
        except Exception as e:
            raise e
    return wrapper

def handle_request(
    func: Callable[..., Awaitable[T]]
) -> Callable[..., Awaitable[dict]]:
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs) -> dict:
        result = await func(request, *args, **kwargs)

        pagination = getattr(request.state, 'pagination', None)
        if pagination and isinstance(pagination, PaginationInfo):
            return PaginatedResponse(
                code=200,
                msg="Success",
                data=result,
                pagination=pagination
            ).model_dump()

        return SuccessResponse.success(result).model_dump()
    return wrapper
