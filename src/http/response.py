from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    code: int
    msg: str
    data: T | None = None

    @classmethod
    def success(
        cls,
        data: T | None = None,
        msg: str = "success",
        code: int = 200,
    ) -> "Response[T]":
        return cls(code=code, msg=msg, data=data)

    @classmethod
    def error(
        cls,
        code: int,
        msg: str,
        data: T | None = None,
    ) -> "Response[T]":
        return cls(code=code, msg=msg, data=data)
