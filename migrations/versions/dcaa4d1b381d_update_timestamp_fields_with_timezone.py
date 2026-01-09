"""update_timestamp_fields_with_timezone

Revision ID: dcaa4d1b381d
Revises: 9f5f1dfe3a30
Create Date: 2026-01-09 22:15:58.804158

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "dcaa4d1b381d"
down_revision: Union[str, Sequence[str], None] = "9f5f1dfe3a30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "sqlite":
        pass
    elif dialect == "postgresql":
        op.alter_column(
            "audit_logs",
            "occurred_at",
            existing_type=postgresql.TIMESTAMP(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )

        op.drop_index(op.f("ix_audit_logs_request_id"), table_name="audit_logs")
        op.drop_constraint(
            op.f("audit_logs_actor_id_fkey"), "audit_logs", type_="foreignkey"
        )
        op.create_foreign_key(
            "audit_logs_actor_id_fkey_new", "audit_logs", "users", ["actor_id"], ["id"]
        )

        op.alter_column(
            "permissions",
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        op.alter_column(
            "permissions",
            "updated_at",
            existing_type=postgresql.TIMESTAMP(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )

        op.drop_constraint(
            op.f("role_permissions_permission_id_fkey"),
            "role_permissions",
            type_="foreignkey",
        )
        op.drop_constraint(
            op.f("role_permissions_role_id_fkey"),
            "role_permissions",
            type_="foreignkey",
        )
        op.create_foreign_key(
            "role_permissions_role_id_fkey_new",
            "role_permissions",
            "roles",
            ["role_id"],
            ["id"],
        )
        op.create_foreign_key(
            "role_permissions_permission_id_fkey_new",
            "role_permissions",
            "permissions",
            ["permission_id"],
            ["id"],
        )

        op.alter_column(
            "roles",
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        op.alter_column(
            "roles",
            "updated_at",
            existing_type=postgresql.TIMESTAMP(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )

        op.drop_constraint(
            op.f("user_roles_user_id_fkey"), "user_roles", type_="foreignkey"
        )
        op.drop_constraint(
            op.f("user_roles_role_id_fkey"), "user_roles", type_="foreignkey"
        )
        op.create_foreign_key(
            "user_roles_role_id_fkey_new", "user_roles", "roles", ["role_id"], ["id"]
        )
        op.create_foreign_key(
            "user_roles_user_id_fkey_new", "user_roles", "users", ["user_id"], ["id"]
        )

        op.alter_column(
            "users",
            "created_at",
            existing_type=postgresql.TIMESTAMP(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
        )
        op.alter_column(
            "users",
            "updated_at",
            existing_type=postgresql.TIMESTAMP(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
        )
        op.alter_column(
            "users",
            "hashed_password",
            existing_type=sa.VARCHAR(length=255),
            type_=sqlmodel.sql.sqltypes.AutoString(length=1024),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "sqlite":
        pass
    elif dialect == "postgresql":
        op.alter_column(
            "users",
            "hashed_password",
            existing_type=sqlmodel.sql.sqltypes.AutoString(length=1024),
            type_=sa.VARCHAR(length=255),
            existing_nullable=False,
        )
        op.alter_column(
            "users",
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            type_=postgresql.TIMESTAMP(),
            existing_nullable=False,
        )
        op.alter_column(
            "users",
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            type_=postgresql.TIMESTAMP(),
            existing_nullable=False,
        )

        op.drop_constraint(
            "user_roles_role_id_fkey_new", "user_roles", type_="foreignkey"
        )
        op.drop_constraint(
            "user_roles_user_id_fkey_new", "user_roles", type_="foreignkey"
        )
        op.create_foreign_key(
            op.f("user_roles_role_id_fkey"),
            "user_roles",
            "roles",
            ["role_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_foreign_key(
            op.f("user_roles_user_id_fkey"),
            "user_roles",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )

        op.alter_column(
            "roles",
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            type_=postgresql.TIMESTAMP(),
            existing_nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        op.alter_column(
            "roles",
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            type_=postgresql.TIMESTAMP(),
            existing_nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )

        op.drop_constraint(
            "role_permissions_role_id_fkey_new", "role_permissions", type_="foreignkey"
        )
        op.drop_constraint(
            "role_permissions_permission_id_fkey_new",
            "role_permissions",
            type_="foreignkey",
        )
        op.create_foreign_key(
            op.f("role_permissions_role_id_fkey"),
            "role_permissions",
            "roles",
            ["role_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_foreign_key(
            op.f("role_permissions_permission_id_fkey"),
            "role_permissions",
            "permissions",
            ["permission_id"],
            ["id"],
            ondelete="CASCADE",
        )

        op.alter_column(
            "permissions",
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            type_=postgresql.TIMESTAMP(),
            existing_nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        op.alter_column(
            "permissions",
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            type_=postgresql.TIMESTAMP(),
            existing_nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )

        op.drop_constraint(
            "audit_logs_actor_id_fkey_new", "audit_logs", type_="foreignkey"
        )
        op.create_foreign_key(
            op.f("audit_logs_actor_id_fkey"),
            "audit_logs",
            "users",
            ["actor_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(
            op.f("ix_audit_logs_request_id"), "audit_logs", ["request_id"], unique=False
        )

        op.alter_column(
            "audit_logs",
            "occurred_at",
            existing_type=sa.DateTime(timezone=True),
            type_=postgresql.TIMESTAMP(),
            existing_nullable=False,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )
