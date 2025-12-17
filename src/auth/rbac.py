from collections.abc import Callable
from typing import Literal, overload

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings, get_settings
from src.core.schemas import User
from src.core.schemas.error import ErrorCode
from src.exceptions import BusinessException, InsufficientPermissionException
from src.session import get_session

from .permission_service import PermissionService
from . import current_user


class RBACDependencies:
    def __init__(
        self,
        permission_service: PermissionService,
        bypass_superuser: bool = True,
        wildcard_support: bool = True,
    ):
        self.permission_service = permission_service
        self.bypass_superuser = bypass_superuser
        self.wildcard_support = wildcard_support

    def require_permissions(
        self,
        *perms: str,
        match: Literal["all", "any"] = "all",
        bypass_superuser: bool | None = None,
        wildcard_support: bool | None = None,
    ) -> Callable:
        async def dependency(user: User = Depends(current_user)) -> None:
            bypass = (
                bypass_superuser
                if bypass_superuser is not None
                else self.bypass_superuser
            )
            if bypass and user.is_superuser:
                return

            wildcard = (
                wildcard_support
                if wildcard_support is not None
                else self.wildcard_support
            )
            has_perms = await self.permission_service.check_permissions(
                user_id=user.id,
                required_perms=perms,
                match=match,
                wildcard_support=wildcard,
            )

            if not has_perms:
                user_perms = await self.permission_service.get_user_permissions(user.id)
                raise InsufficientPermissionException(
                    user_id=user.id,
                    required=list(perms),
                    user_perms=user_perms,
                )

        return dependency

    def require_roles(
        self,
        *roles: str,
        match: Literal["all", "any"] = "all",
        bypass_superuser: bool | None = None,
    ) -> Callable:
        async def dependency(user: User = Depends(current_user)) -> None:
            bypass = (
                bypass_superuser
                if bypass_superuser is not None
                else self.bypass_superuser
            )
            if bypass and user.is_superuser:
                return

            has_roles = await self.permission_service.check_roles(
                user_id=user.id,
                required_roles=roles,
                match=match,
            )

            if not has_roles:
                user_roles = await self.permission_service.get_user_roles(user.id)
                raise BusinessException(
                    code=ErrorCode.PERM_INSUFFICIENT,
                    msg=f"User {user.id} lacks required roles",
                    data={
                        "required": list(roles),
                        "user_roles": list(user_roles),
                        "user_id": user.id,
                    },
                )

        return dependency

    @overload
    def owner_or_perm(
        self,
        get_owner_id: Callable[..., int],
        perms: str,
        match: Literal["all", "any"] = "all",
        bypass_superuser: bool | None = None,
        wildcard_support: bool | None = None,
    ) -> Callable: ...

    @overload
    def owner_or_perm(
        self,
        get_owner_id: Callable[..., int],
        perms: list[str],
        match: Literal["all", "any"] = "all",
        bypass_superuser: bool | None = None,
        wildcard_support: bool | None = None,
    ) -> Callable: ...

    def owner_or_perm(
        self,
        get_owner_id: Callable[..., int],
        perms: str | list[str],
        match: Literal["all", "any"] = "all",
        bypass_superuser: bool | None = None,
        wildcard_support: bool | None = None,
    ) -> Callable:
        async def dependency(
            owner_id: int = Depends(get_owner_id),
            user: User = Depends(current_user),
        ) -> None:
            bypass = (
                bypass_superuser
                if bypass_superuser is not None
                else self.bypass_superuser
            )
            if bypass and user.is_superuser:
                return

            if user.id == owner_id:
                return

            perms_list = [perms] if isinstance(perms, str) else list(perms)
            wildcard = (
                wildcard_support
                if wildcard_support is not None
                else self.wildcard_support
            )

            has_perms = await self.permission_service.check_permissions(
                user_id=user.id,
                required_perms=perms_list,
                match=match,
                wildcard_support=wildcard,
            )

            if not has_perms:
                user_perms = await self.permission_service.get_user_permissions(user.id)
                raise InsufficientPermissionException(
                    user_id=user.id,
                    required=perms_list,
                    user_perms=user_perms,
                )

        return dependency


async def get_rbac_deps(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> RBACDependencies:
    permission_service = PermissionService(session=session)

    return RBACDependencies(
        permission_service=permission_service,
        bypass_superuser=(
            settings.rbac.bypass_superuser if hasattr(settings, "rbac") else True
        ),
        wildcard_support=(
            settings.rbac.wildcard_support if hasattr(settings, "rbac") else True
        ),
    )


def require_permissions(
    *perms: str,
    match: Literal["all", "any"] = "all",
    bypass_superuser: bool | None = None,
    wildcard_support: bool | None = None,
):
    async def dependency(
        rbac_deps: RBACDependencies = Depends(get_rbac_deps),
        user: User = Depends(current_user),
    ):
        perm_dep = rbac_deps.require_permissions(
            *perms,
            match=match,
            bypass_superuser=bypass_superuser,
            wildcard_support=wildcard_support,
        )
        return await perm_dep(user=user)

    return Depends(dependency)


def require_roles(
    *roles: str,
    match: Literal["all", "any"] = "all",
    bypass_superuser: bool | None = None,
):
    async def dependency(
        rbac_deps: RBACDependencies = Depends(get_rbac_deps),
        user: User = Depends(current_user),
    ):
        role_dep = rbac_deps.require_roles(
            *roles,
            match=match,
            bypass_superuser=bypass_superuser,
        )
        return await role_dep(user=user)

    return Depends(dependency)


def owner_or_perm(
    get_owner_id: Callable[..., int],
    perms: str | list[str],
    match: Literal["all", "any"] = "all",
    bypass_superuser: bool | None = None,
    wildcard_support: bool | None = None,
):
    async def dependency(
        owner_id: int = Depends(get_owner_id),
        rbac_deps: RBACDependencies = Depends(get_rbac_deps),
        user: User = Depends(current_user),
    ):
        owner_perm_dep = rbac_deps.owner_or_perm(
            get_owner_id=get_owner_id,
            perms=perms,
            match=match,
            bypass_superuser=bypass_superuser,
            wildcard_support=wildcard_support,
        )
        return await owner_perm_dep(user=user, owner_id=owner_id)

    return Depends(dependency)
