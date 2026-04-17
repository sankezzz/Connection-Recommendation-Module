"""create_user_embeddings_table

Revision ID: b5e7f9a2c3d1
Revises: 3f8a2c1d9e74
Create Date: 2026-04-16 17:00:00.000000

Adds user_embeddings table.
Populated automatically on profile create / update.

Schema
------
user_id     UUID PK FK → users.id
is_vector   JSONB        11-dim IS vector (list[float])
             Layout: [3 commodity | 3 role | 3 geo | 2 qty]
updated_at  TIMESTAMP    set on every upsert
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b5e7f9a2c3d1"
down_revision: Union[str, None] = "3f8a2c1d9e74"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_embeddings",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("is_vector", postgresql.JSONB(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_embeddings")
