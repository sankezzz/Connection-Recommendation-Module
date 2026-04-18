"""merge heads

Revision ID: d258688090c7
Revises: cbd15ef96636, f3a9b1c2d8e4
Create Date: 2026-04-18

Merges news branch (cbd15ef96636) and post-recommendation branch (f3a9b1c2d8e4).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd258688090c7'
down_revision: Union[str, None] = ('cbd15ef96636', 'f3a9b1c2d8e4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
