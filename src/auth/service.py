from collections.abc import Sequence
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from .repository import PermissionRepository


class PermissionService:
    def __init__(
        self,
        session: AsyncSession,
        repository: PermissionRepository | None = None,
    ):
        self.repository = repository or PermissionRepository(session)

    @staticmethod
    def _split_permission(perm: str) -> tuple[str, str | None]:
        """Split permission into (module, action)."""
        if ":" in perm:
            module, action = perm.split(":", 1)
            # Treat empty action as absent (not a wildcard).
            return module, action if action != "" else None
        return perm, None

    def _match_permission(
        self,
        required_perm: str,
        user_perm: str,
        wildcard_support: bool,
    ) -> bool:
        if not wildcard_support:
            return required_perm == user_perm

        if required_perm == "":
            return True

        if required_perm == "*":
            return user_perm == "*"
        if user_perm == "*":
            return True

        req_module, req_action = self._split_permission(required_perm)
        user_module, user_action = self._split_permission(user_perm)

        if req_module != user_module:
            return False

        if req_action is None:
            return user_action is None

        if req_action == "*":
            return True

        if user_action is None:
            return False

        return user_action == req_action or user_action == "*"

    async def get_user_permissions(self, user_id: int) -> set[str]:
        return await self.repository.get_user_permissions(user_id)

    async def get_user_roles(self, user_id: int) -> set[str]:
        return await self.repository.get_user_roles(user_id)

    async def check_permissions(
        self,
        user_id: int,
        required_perms: Sequence[str],
        match: Literal["all", "any"] = "all",
        wildcard_support: bool = True,
    ) -> bool:
        user_perms = await self.get_user_permissions(user_id)

        if not required_perms:
            return True

        matched = []
        for required_perm in required_perms:
            matched.append(
                any(
                    self._match_permission(required_perm, user_perm, wildcard_support)
                    for user_perm in user_perms
                ),
            )

        return all(matched) if match == "all" else any(matched)

    async def check_roles(
        self,
        user_id: int,
        required_roles: Sequence[str],
        match: Literal["all", "any"] = "all",
    ) -> bool:
        user_roles = await self.get_user_roles(user_id)

        if not required_roles:
            return True

        matched = [required_role in user_roles for required_role in required_roles]

        return all(matched) if match == "all" else any(matched)
