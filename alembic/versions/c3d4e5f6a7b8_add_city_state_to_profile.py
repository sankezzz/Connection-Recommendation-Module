"""add_city_state_to_profile

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('profile', sa.Column('city', sa.String(100), nullable=True))
    op.add_column('profile', sa.Column('state', sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column('profile', 'state')
    op.drop_column('profile', 'city')
