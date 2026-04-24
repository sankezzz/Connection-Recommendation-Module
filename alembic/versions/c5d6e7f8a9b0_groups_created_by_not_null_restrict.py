"""groups_created_by_not_null_restrict

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-04-24

groups.created_by was originally NOT NULL (see 3f8a2c1d9e74) but the model
drifted to nullable=True / SET NULL.  This migration re-aligns the DB:
  1. Deletes any groups with no creator (prevents NOT NULL violation).
  2. Enforces NOT NULL on the column.
  3. Replaces the FK with ON DELETE RESTRICT so deleting a user who owns
     a group is explicitly blocked rather than silently nulling the field.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c5d6e7f8a9b0"
down_revision: Union[str, None] = "b4c5d6e7f8a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop orphaned groups before tightening the constraint
    op.execute("DELETE FROM groups WHERE created_by IS NULL")

    op.alter_column("groups", "created_by", nullable=False)

    op.drop_constraint("groups_created_by_fkey", "groups", type_="foreignkey")
    op.create_foreign_key(
        "groups_created_by_fkey",
        "groups",
        "users",
        ["created_by"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("groups_created_by_fkey", "groups", type_="foreignkey")
    op.create_foreign_key(
        "groups_created_by_fkey",
        "groups",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.alter_column("groups", "created_by", nullable=True)
