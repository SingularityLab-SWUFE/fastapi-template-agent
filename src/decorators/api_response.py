from typing import TypeVar, Callable, Any, overload, Awaitable
from functools import wraps
import inspect

from fastapi import HTTPException
from src.responses import JsonResponse

T = TypeVar("T")

def _extract_error_code(exception: Exception) -> int:
    """从异常中提取错误码"""
    if isinstance(exception, HTTPException):
        # HTTP状态码 * 100 映射到错误码范围
        error_code = exception.status_code * 100
        # 确保错误码在有效范围内
        if 10000 <= error_code <= 99999:
            return error_code
    # 默认通用错误码
    return 50000

def _wrap_sync_response(func: Callable[..., T]) -> Callable[..., JsonResponse[T]]:
    @wraps(func)
    def wrapper(*args, **kwargs) -> JsonResponse[T]:
        try:
            result = func(*args, **kwargs)
            if isinstance(result, JsonResponse):
                return result
            return JsonResponse.success(result)
        except Exception as e:
            error_code = _extract_error_code(e)
            error_msg = str(e)
            return JsonResponse.error(error_code, error_msg)
    return wrapper

def _wrap_async_response(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[JsonResponse[T]]]:
    @wraps(func)
    async def wrapper(*args, **kwargs) -> JsonResponse[T]:
        try:
            result = await func(*args, **kwargs)
            if isinstance(result, JsonResponse):
                return result
            return JsonResponse.success(result)
        except Exception as e:
            error_code = _extract_error_code(e)
            error_msg = str(e)
            return JsonResponse.error(error_code, error_msg)
    return wrapper

@overload
def api_response(func: Callable[..., T]) -> Callable[..., JsonResponse[T]]: ...

@overload
def api_response(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[JsonResponse[T]]]: ...

def api_response(func: Callable[..., Any]) -> Callable[..., Any]:
    if inspect.iscoroutinefunction(func):
        return _wrap_async_response(func)
    return _wrap_sync_response(func)