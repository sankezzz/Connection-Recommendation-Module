"""create_business_table

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-05-13

Moves business_name, city, state, latitude, longitude off profile
into a dedicated business table (1:1 with profile). Existing profile
rows are migrated before the columns are dropped.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'business',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('business_name', sa.String(100), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['profile.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('profile_id', name='uq_business_profile'),
    )

    op.execute("""
        INSERT INTO business (profile_id, business_name, city, state, latitude, longitude)
        SELECT id, business_name, city, state, latitude, longitude FROM profile
    """)

    op.drop_column('profile', 'business_name')
    op.drop_column('profile', 'city')
    op.drop_column('profile', 'state')
    op.drop_column('profile', 'latitude')
    op.drop_column('profile', 'longitude')


def downgrade() -> None:
    op.add_column('profile', sa.Column('longitude', sa.Float(), nullable=True))
    op.add_column('profile', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('profile', sa.Column('state', sa.String(100), nullable=True))
    op.add_column('profile', sa.Column('city', sa.String(100), nullable=True))
    op.add_column('profile', sa.Column('business_name', sa.String(100), nullable=True))

    op.execute("""
        UPDATE profile p
        SET business_name = b.business_name,
            city          = b.city,
            state         = b.state,
            latitude      = b.latitude,
            longitude     = b.longitude
        FROM business b
        WHERE b.profile_id = p.id
    """)

    op.drop_table('business')
