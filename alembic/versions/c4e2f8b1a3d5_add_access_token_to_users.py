"""add access_token to users

Revision ID: c4e2f8b1a3d5
Revises: d7e3f1a4c2b9
Create Date: 2026-04-16

Stores the lifetime MVP access token alongside the user row so returning
users get the same token back on OTP re-verify instead of a fresh one.
"""
from alembic import op
import sqlalchemy as sa

revision = "c4e2f8b1a3d5"
down_revision = "d7e3f1a4c2b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("access_token", sa.String(2000), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "access_token")
