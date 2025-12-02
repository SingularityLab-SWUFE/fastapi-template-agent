from typing import Generic, TypeVar, Literal

from pydantic import BaseModel, model_validator


T = TypeVar("T")


class JsonResponse(BaseModel, Generic[T]):
    success: bool
    code: Literal[200] | int
    data: T | None = None
    error: dict[str, int | str] | None = None

    @model_validator(mode='after')
    def validate_response(self) -> 'JsonResponse[T]':
        if self.success:
            if self.code != 200:
                raise ValueError('success=True requires code=200')
            if self.error is not None:
                raise ValueError('success=True requires error=None')
        else:
            if self.data is not None:
                raise ValueError('success=False requires data=None')
        return self

def _json_response_success(cls: type[JsonResponse], data: T) -> JsonResponse[T]:
    return cls(success=True, code=200, data=data, error=None)


def _json_response_error(cls: type[JsonResponse], code: int, msg: str) -> JsonResponse[None]:
    if not (10000 <= code <= 99999):
        raise ValueError(f"Error code must be between 10000 and 99999, got {code}")
    return cls(success=False, code=code, data=None, error={"code": code, "msg": msg})


JsonResponse.success = classmethod(_json_response_success)  # type: ignore
JsonResponse.error = classmethod(_json_response_error)  # type: ignore

