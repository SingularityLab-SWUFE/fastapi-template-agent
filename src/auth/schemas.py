from typing import Literal

from fastapi_users import schemas
from pydantic import BaseModel


class UserRead(schemas.BaseUser[int]):
    username: str


class UserCreate(schemas.BaseUserCreate):
    username: str


class UserUpdate(schemas.BaseUserUpdate):
    username: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["Bearer"] = "Bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"


class MessageResponse(BaseModel):
    detail: str
