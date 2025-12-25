"""add request_id to audit logs

Revision ID: 9f5f1dfe3a30
Revises: 74c1a3bca7fb
Create Date: 2025-12-23 18:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = "9f5f1dfe3a30"
down_revision: Union[str, Sequence[str], None] = "74c1a3bca7fb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "audit_logs",
        sa.Column(
            "request_id", sqlmodel.sql.sqltypes.AutoString(length=36), nullable=True
        ),
    )
    op.create_index(
        "ix_audit_logs_request_id", "audit_logs", ["request_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_request_id", table_name="audit_logs")
    op.drop_column("audit_logs", "request_id")
