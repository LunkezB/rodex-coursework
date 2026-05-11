"""Add full_name to users

Revision ID: 0002_add_user_full_name
Revises: 0001_initial_schema
Create Date: 2026-05-02
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_add_user_full_name"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("full_name", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "full_name")
