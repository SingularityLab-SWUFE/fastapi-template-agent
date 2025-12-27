from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from src.audit import AuditService, get_audit_service
from src.audit.schemas import AuditAction, AuditResult
from src.audit.service import extract_client_info
from src.auth import fastapi_users
from src.auth.backend import (
    RefreshTokenManager,
    get_jwt_strategy,
    get_refresh_token_manager,
)
from src.auth.manager import UserManager, get_user_manager
from src.auth.schemas import (
    AccessTokenResponse,
    MessageResponse,
    TokenResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)
from src.shared.errors import ErrorCode
from src.exceptions import BusinessException

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
    audit_service: AuditService = Depends(get_audit_service),
) -> TokenResponse:
    user_agent, ip = extract_client_info(request)

    user = await user_manager.authenticate(credentials)
    if not user or not user.is_active:
        await audit_service.log(
            action=AuditAction.LOGIN,
            result=AuditResult.FAILURE,
            user_agent=user_agent,
            ip=ip,
            extra={"username": credentials.username},
        )
        raise BusinessException(
            ErrorCode.AUTH_INVALID_CREDENTIALS, "Invalid credentials"
        )

    access_token = await strategy.write_token(user)

    refresh_token = await refresh_manager.create_refresh_token(user.id, user_agent)

    await audit_service.log(
        action=AuditAction.LOGIN,
        result=AuditResult.SUCCESS,
        actor_id=user.id,
        user_agent=user_agent,
        ip=ip,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
    )


@router.post("/jwt/refresh")
async def refresh_jwt(
    request: Request,
    refresh_token: str,
    user_manager: UserManager = Depends(get_user_manager),
    strategy=Depends(get_jwt_strategy),
    refresh_manager: RefreshTokenManager = Depends(get_refresh_token_manager),
    audit_service: AuditService = Depends(get_audit_service),
) -> AccessTokenResponse:
    user_agent, ip = extract_client_info(request)

    user_id = await refresh_manager.verify_refresh_token(refresh_token)

    if not user_id:
        await audit_service.log(
            action=AuditAction.REFRESH,
            result=AuditResult.FAILURE,
            user_agent=user_agent,
            ip=ip,
        )
        raise BusinessException(ErrorCode.AUTH_TOKEN_INVALID, "Invalid token")

    user = await user_manager.get(user_id)
    if not user or not user.is_active:
        await audit_service.log(
            action=AuditAction.REFRESH,
            result=AuditResult.FAILURE,
            actor_id=user_id,
            user_agent=user_agent,
            ip=ip,
        )
        raise BusinessException(ErrorCode.USER_INACTIVE, "User inactive")

    access_token = await strategy.write_token(user)

    await audit_service.log(
        action=AuditAction.REFRESH,
        result=AuditResult.SUCCESS,
        actor_id=user.id,
        user_agent=user_agent,
        ip=ip,
    )

    return AccessTokenResponse(access_token=access_token, token_type="Bearer")


@router.post("/jwt/logout")
async def logout(
    request: Request,
    refresh_token: str,
    refresh_manager: RefreshTokenManager = Depends(get_refresh_token_manager),
    audit_service: AuditService = Depends(get_audit_service),
) -> MessageResponse:
    user_agent, ip = extract_client_info(request)
    user_id = await refresh_manager.verify_refresh_token(refresh_token)

    if not user_id:
        await audit_service.log(
            action=AuditAction.LOGOUT,
            result=AuditResult.FAILURE,
            user_agent=user_agent,
            ip=ip,
        )
        raise BusinessException(ErrorCode.AUTH_TOKEN_INVALID, "Invalid token")

    await refresh_manager.revoke_token(refresh_token)

    await audit_service.log(
        action=AuditAction.LOGOUT,
        result=AuditResult.SUCCESS,
        actor_id=user_id,
        user_agent=user_agent,
        ip=ip,
    )

    return MessageResponse(detail="Successfully logged out")
