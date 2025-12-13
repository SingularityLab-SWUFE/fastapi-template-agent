from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from src.exceptions import BusinessException, ErrorCode

from . import fastapi_users
from .backend import RefreshTokenManager, get_jwt_strategy, get_refresh_token_manager
from .manager import UserManager, get_user_manager
from .schemas import (
    AccessTokenResponse,
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
    user_manager: UserManager = Depends(get_user_manager),
    strategy=Depends(get_jwt_strategy),
    refresh_manager: RefreshTokenManager = Depends(get_refresh_token_manager),
) -> TokenResponse:
    user = await user_manager.authenticate(credentials)
    if not user or not user.is_active:
        raise BusinessException(
            ErrorCode.AUTH_INVALID_CREDENTIALS, "Invalid credentials"
        )

    access_token = await strategy.write_token(user)

    device_info = request.headers.get("user-agent")
    refresh_token = await refresh_manager.create_refresh_token(user.id, device_info)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
    )


@router.post("/jwt/refresh")
async def refresh_jwt(
    refresh_token: str,
    user_manager: UserManager = Depends(get_user_manager),
    strategy=Depends(get_jwt_strategy),
    refresh_manager: RefreshTokenManager = Depends(get_refresh_token_manager),
) -> AccessTokenResponse:
    user_id = await refresh_manager.verify_refresh_token(refresh_token)

    if not user_id:
        raise BusinessException(ErrorCode.AUTH_TOKEN_INVALID, "Invalid token")

    user = await user_manager.get(user_id)
    if not user or not user.is_active:
        raise BusinessException(ErrorCode.USER_INACTIVE, "User inactive")

    access_token = await strategy.write_token(user)

    return AccessTokenResponse(access_token=access_token, token_type="Bearer")


@router.post("/jwt/logout")
async def logout(
    refresh_token: str,
    refresh_manager: RefreshTokenManager = Depends(get_refresh_token_manager),
) -> MessageResponse:
    await refresh_manager.revoke_token(refresh_token)
    return MessageResponse(detail="Successfully logged out")
