"""add audit log table

Revision ID: 74c1a3bca7fb
Revises: 5b7a7f7f3f6a
Create Date: 2025-12-21 16:46:11.195833

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "74c1a3bca7fb"
down_revision: Union[str, Sequence[str], None] = "5b7a7f7f3f6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column(
            "action", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False
        ),
        sa.Column(
            "resource_type", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True
        ),
        sa.Column("resource_id", sa.Text(), nullable=True),
        sa.Column(
            "result", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False
        ),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip", sqlmodel.sql.sqltypes.AutoString(length=45), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"])
    op.create_index(op.f("ix_audit_logs_actor_id"), "audit_logs", ["actor_id"])
    op.create_index(op.f("ix_audit_logs_occurred_at"), "audit_logs", ["occurred_at"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_occurred_at"), table_name="audit_logs")
    op.drop_table("audit_logs")
