from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field
from sqlmodel import SQLModel

T = TypeVar('T')

class ResponseBase(SQLModel, Generic[T]):
    code: int = Field(..., description="响应码")
    msg: str = Field(..., description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")

class SuccessResponse(ResponseBase[T], Generic[T]):
    @classmethod
    def success(cls, data: T, msg: str = "Success") -> "SuccessResponse[T]":
        return cls(code=200, msg=msg, data=data)

class ErrorResponse(ResponseBase[None]):
    @classmethod
    def error(cls, code: int, msg: str) -> "ErrorResponse":
        return cls(code=code, msg=msg, data=None)

class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int

class PaginatedResponse(ResponseBase[list[T]]):
    pagination: PaginationInfo
