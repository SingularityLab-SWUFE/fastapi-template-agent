from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from src.auth import fastapi_users
from src.auth.service import AuthenticationService, get_auth_service
from src.auth.schemas import (
    MessageResponse,
    TokenResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)

router = APIRouter()

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


@router.post("/jwt/login")
async def login(
    request: Request,
    credentials: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> TokenResponse:
    return await auth_service.login(credentials, request)


@router.post("/jwt/refresh")
async def refresh_jwt(
    request: Request,
    refresh_token: str,
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> TokenResponse:
    return await auth_service.refresh(refresh_token, request)


@router.post("/jwt/logout")
async def logout(
    request: Request,
    refresh_token: str,
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> MessageResponse:
    await auth_service.logout(refresh_token, request)
    return MessageResponse(detail="Successfully logged out")
