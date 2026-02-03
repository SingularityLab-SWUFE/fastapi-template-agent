from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from src.audit import AuditService, get_audit_service
from src.audit.schemas import AuditAction, AuditResult
from src.http.utils import extract_client_info
from src.auth.backend import (
    RefreshTokenManager,
    get_jwt_strategy,
    get_refresh_token_manager,
)
from src.auth.manager import UserManager, get_user_manager
from src.auth.schemas import TokenResponse
from src.shared.errors import ErrorCode
from src.exceptions import BusinessException


class AuthenticationService:
    def __init__(
        self,
        user_manager: UserManager,
        strategy,
        refresh_manager: RefreshTokenManager,
        audit_service: AuditService,
    ):
        self.user_manager = user_manager
        self.strategy = strategy
        self.refresh_manager = refresh_manager
        self.audit_service = audit_service

    async def login(
        self, credentials: OAuth2PasswordRequestForm, request: Request
    ) -> TokenResponse:
        user_agent, ip = extract_client_info(request)

        user = await self.user_manager.authenticate(credentials)
        if not user or not user.is_active:
            await self.audit_service.log(
                action=AuditAction.LOGIN,
                result=AuditResult.FAILURE,
                user_agent=user_agent,
                ip=ip,
                extra={"username": credentials.username},
            )
            raise BusinessException(
                ErrorCode.AUTH_INVALID_CREDENTIALS, "Invalid credentials"
            )

        access_token = await self.strategy.write_token(user)
        refresh_token = await self.refresh_manager.create_refresh_token(
            user.id, user_agent
        )

        await self.audit_service.log(
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

    async def refresh(self, refresh_token: str, request: Request) -> TokenResponse:
        user_agent, ip = extract_client_info(request)

        user_id = await self.refresh_manager.verify_refresh_token(refresh_token)

        if not user_id:
            await self.audit_service.log(
                action=AuditAction.REFRESH,
                result=AuditResult.FAILURE,
                user_agent=user_agent,
                ip=ip,
            )
            raise BusinessException(ErrorCode.AUTH_TOKEN_INVALID, "Invalid token")

        user = await self.user_manager.get(user_id)
        if not user or not user.is_active:
            await self.audit_service.log(
                action=AuditAction.REFRESH,
                result=AuditResult.FAILURE,
                actor_id=user_id,
                user_agent=user_agent,
                ip=ip,
            )
            raise BusinessException(ErrorCode.USER_INACTIVE, "User inactive")

        access_token = await self.strategy.write_token(user)
        new_refresh_token = await self.refresh_manager.create_refresh_token(
            user.id, user_agent
        )
        await self.refresh_manager.revoke_token(refresh_token)

        await self.audit_service.log(
            action=AuditAction.REFRESH,
            result=AuditResult.SUCCESS,
            actor_id=user.id,
            user_agent=user_agent,
            ip=ip,
        )

        return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)

    async def logout(self, refresh_token: str, request: Request) -> None:
        user_agent, ip = extract_client_info(request)
        user_id = await self.refresh_manager.verify_refresh_token(refresh_token)

        if not user_id:
            await self.audit_service.log(
                action=AuditAction.LOGOUT,
                result=AuditResult.FAILURE,
                user_agent=user_agent,
                ip=ip,
            )
            raise BusinessException(ErrorCode.AUTH_TOKEN_INVALID, "Invalid token")

        await self.refresh_manager.revoke_token(refresh_token)

        await self.audit_service.log(
            action=AuditAction.LOGOUT,
            result=AuditResult.SUCCESS,
            actor_id=user_id,
            user_agent=user_agent,
            ip=ip,
        )


async def get_auth_service(
    user_manager: UserManager = Depends(get_user_manager),
    strategy=Depends(get_jwt_strategy),
    refresh_manager: RefreshTokenManager = Depends(get_refresh_token_manager),
    audit_service: AuditService = Depends(get_audit_service),
) -> AuthenticationService:
    return AuthenticationService(user_manager, strategy, refresh_manager, audit_service)
