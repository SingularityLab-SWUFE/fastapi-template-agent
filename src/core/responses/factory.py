from typing import TypeVar

from .schemas import JsonResponse

T = TypeVar("T")


def success_response(data: T) -> JsonResponse[T]:
    return JsonResponse.success(data)


def error_response(code: int, msg: str) -> JsonResponse[None]:
    return JsonResponse.error(code, msg)
