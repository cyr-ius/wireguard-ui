"""add auth_source column to users table

Revision ID: 0003
Revises: 0001
Create Date: 2026-04-19
"""

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "auth_source", sa.String(length=20), nullable=False, server_default="local"
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "auth_source")
