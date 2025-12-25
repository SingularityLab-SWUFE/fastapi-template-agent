import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.auth.models import Permission, Role, RolePermission, UserRole


class TestRoleSchema:
    async def test_create_role(self, test_db):
        async with test_db() as session:
            role = Role(name="moderator", description="Moderator role", is_system=False)
            session.add(role)
            await session.commit()
            await session.refresh(role)

            assert role.id is not None
            assert role.name == "moderator"
            assert role.is_system is False
            assert role.created_at is not None
            assert role.updated_at is not None

    async def test_role_name_unique_constraint(self, test_db):
        async with test_db() as session:
            session.add(Role(name="duplicate", is_system=False))
            await session.commit()

            session.add(Role(name="duplicate", is_system=False))
            with pytest.raises(IntegrityError):
                await session.commit()


class TestPermissionSchema:
    async def test_create_permission(self, test_db):
        async with test_db() as session:
            perm = Permission(
                code="user:delete",
                name="Delete User",
                description="Delete user accounts",
                module="user",
            )
            session.add(perm)
            await session.commit()
            await session.refresh(perm)

            assert perm.id is not None
            assert perm.code == "user:delete"
            assert perm.module == "user"
            assert perm.created_at is not None
            assert perm.updated_at is not None

    async def test_permission_code_unique_constraint(self, test_db):
        async with test_db() as session:
            session.add(Permission(code="user:read", name="Read User", module="user"))
            await session.commit()

            session.add(Permission(code="user:read", name="Read User 2", module="user"))
            with pytest.raises(IntegrityError):
                await session.commit()


class TestUserRoleAssociation:
    async def test_user_role_constraints(self, test_db, test_user):
        async with test_db() as session:
            role = Role(name="member", is_system=False)
            session.add(role)
            await session.commit()
            await session.refresh(role)

            user_role = UserRole(user_id=test_user.id, role_id=role.id)
            session.add(user_role)
            await session.commit()

            assert user_role.user_id == test_user.id
            assert user_role.role_id == role.id
            assert user_role.assigned_at is not None

            session.expunge(user_role)

            duplicate = UserRole(user_id=test_user.id, role_id=role.id)
            session.add(duplicate)
            with pytest.raises(IntegrityError):
                await session.commit()


class TestRolePermissionAssociation:
    async def test_role_permission_constraints(self, test_db):
        async with test_db() as session:
            role = Role(name="editor", is_system=False)
            perm = Permission(code="post:edit", name="Edit Post", module="post")
            session.add_all([role, perm])
            await session.commit()
            await session.refresh(role)
            await session.refresh(perm)

            role_perm = RolePermission(role_id=role.id, permission_id=perm.id)
            session.add(role_perm)
            await session.commit()

            assert role_perm.role_id == role.id
            assert role_perm.permission_id == perm.id
            assert role_perm.assigned_at is not None

            session.expunge(role_perm)

            duplicate = RolePermission(role_id=role.id, permission_id=perm.id)
            session.add(duplicate)
            with pytest.raises(IntegrityError):
                await session.commit()


class TestMigrationSeedData:
    @pytest.mark.parametrize(
        "role_name,expected_desc,expected_system",
        [
            ("admin", "System administrator role", True),
            ("user", "Default user role", True),
        ],
    )
    async def test_system_role_properties(
        self, test_db, role_name, expected_desc, expected_system
    ):
        async with test_db() as session:
            result = await session.execute(select(Role).where(Role.name == role_name))
            role = result.scalar_one_or_none()

            assert role is not None
            assert role.is_system is expected_system
            assert role.description == expected_desc


class TestRBACIntegration:
    async def test_complete_rbac_flow(self, test_db, test_user):
        async with test_db() as session:
            role = Role(name="moderator", description="Moderator role", is_system=False)
            perm1 = Permission(code="post:approve", name="Approve Post", module="post")
            perm2 = Permission(
                code="comment:delete", name="Delete Comment", module="comment"
            )

            session.add_all([role, perm1, perm2])
            await session.commit()
            await session.refresh(role)
            await session.refresh(perm1)
            await session.refresh(perm2)

            role_perm1 = RolePermission(role_id=role.id, permission_id=perm1.id)
            role_perm2 = RolePermission(role_id=role.id, permission_id=perm2.id)
            session.add_all([role_perm1, role_perm2])
            await session.commit()

            user_role = UserRole(user_id=test_user.id, role_id=role.id)
            session.add(user_role)
            await session.commit()

            result = await session.execute(
                select(Permission.code)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .join(Role, Role.id == RolePermission.role_id)
                .join(UserRole, UserRole.role_id == Role.id)
                .where(UserRole.user_id == test_user.id)
            )
            permissions = result.scalars().all()

            assert len(permissions) == 2
            assert "post:approve" in permissions
            assert "comment:delete" in permissions

    async def test_multiple_roles_per_user(self, test_db, test_user):
        async with test_db() as session:
            role1 = Role(name="writer", is_system=False)
            role2 = Role(name="reviewer", is_system=False)
            session.add_all([role1, role2])
            await session.commit()
            await session.refresh(role1)
            await session.refresh(role2)

            session.add(UserRole(user_id=test_user.id, role_id=role1.id))
            session.add(UserRole(user_id=test_user.id, role_id=role2.id))
            await session.commit()

            result = await session.execute(
                select(Role.name)
                .join(UserRole, UserRole.role_id == Role.id)
                .where(UserRole.user_id == test_user.id)
            )
            role_names = result.scalars().all()

            assert len(role_names) == 2
            assert "writer" in role_names
            assert "reviewer" in role_names

    async def test_permission_deduplication_across_roles(self, test_db, test_user):
        async with test_db() as session:
            shared_perm = Permission(code="post:read", name="Read Post", module="post")
            role1 = Role(name="editor", is_system=False)
            role2 = Role(name="viewer", is_system=False)

            session.add_all([shared_perm, role1, role2])
            await session.commit()
            await session.refresh(shared_perm)
            await session.refresh(role1)
            await session.refresh(role2)

            session.add(RolePermission(role_id=role1.id, permission_id=shared_perm.id))
            session.add(RolePermission(role_id=role2.id, permission_id=shared_perm.id))
            session.add(UserRole(user_id=test_user.id, role_id=role1.id))
            session.add(UserRole(user_id=test_user.id, role_id=role2.id))
            await session.commit()

            result = await session.execute(
                select(Permission.code)
                .join(RolePermission, RolePermission.permission_id == Permission.id)
                .join(Role, Role.id == RolePermission.role_id)
                .join(UserRole, UserRole.role_id == Role.id)
                .where(UserRole.user_id == test_user.id)
                .distinct()
            )
            permissions = result.scalars().all()

            assert len(permissions) == 1
            assert permissions[0] == "post:read"
