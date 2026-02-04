from collections.abc import Sequence
from typing import Literal

from .repository import PermissionRepository


class PermissionService:
    def __init__(self, repository: PermissionRepository):
        self.repository = repository

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
        # Wildcard disabled: exact match only
        if not wildcard_support:
            return required_perm == user_perm

        # "*": requires global permission, only user="*" satisfies
        if required_perm == "*":
            return user_perm == "*"
        # user="*": global permission satisfies any requirement
        if user_perm == "*":
            return True

        req_module, req_action = self._split_permission(required_perm)
        user_module, user_action = self._split_permission(user_perm)

        # Different modules: no match
        if req_module != user_module:
            return False

        # required_perm must be "module:action" format (not bare "module")
        if req_action is None:
            return False

        # user has "module" (full module access): matches any "module:action"
        if user_action is None:
            return True

        # "module:*": module wildcard, matches any action
        if req_action == "*":
            return True

        # Exact action match or user has "module:*"
        return user_action == req_action or user_action == "*"

    def _has_permission(
        self,
        required_perm: str,
        user_perms: set[str],
        wildcard_support: bool,
    ) -> bool:
        return any(
            self._match_permission(required_perm, user_perm, wildcard_support)
            for user_perm in user_perms
        )

    async def check_permissions(
        self,
        user_id: int,
        required_perms: Sequence[str],
        match: Literal["all", "any"] = "all",
        wildcard_support: bool = True,
    ) -> bool:
        if match not in ("all", "any"):
            raise ValueError("match must be 'all' or 'any'")

        user_perms = await self.repository.get_user_permissions(user_id)

        if match == "all":
            return all(
                self._has_permission(req, user_perms, wildcard_support)
                for req in required_perms
            )
        return any(
            self._has_permission(req, user_perms, wildcard_support)
            for req in required_perms
        )

    async def check_roles(
        self,
        user_id: int,
        required_roles: Sequence[str],
        match: Literal["all", "any"] = "all",
    ) -> bool:
        if match not in ("all", "any"):
            raise ValueError("match must be 'all' or 'any'")

        user_roles = await self.repository.get_user_roles(user_id)

        if match == "all":
            return all(req in user_roles for req in required_roles)
        return any(req in user_roles for req in required_roles)
