from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Permission, Role, RolePermission, UserRole


class PermissionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_permissions(self, user_id: int) -> set[str]:
        stmt = (
            select(Permission.code)
            .distinct()
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(UserRole, RolePermission.role_id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return set(result.scalars().all())

    async def get_user_roles(self, user_id: int) -> set[str]:
        stmt = (
            select(Role.name)
            .distinct()
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return set(result.scalars().all())
