"""add_cascade_on_profile_child_fks

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-22

profile_commodities, profile_interests, profile_documents all reference
profile.id without ON DELETE CASCADE. When a user is deleted, the DB
cascade reaches profile but then fails on these child tables.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('profile_commodities_profile_id_fkey', 'profile_commodities', type_='foreignkey')
    op.create_foreign_key(
        'profile_commodities_profile_id_fkey', 'profile_commodities', 'profile',
        ['profile_id'], ['id'], ondelete='CASCADE',
    )

    op.drop_constraint('profile_interests_profile_id_fkey', 'profile_interests', type_='foreignkey')
    op.create_foreign_key(
        'profile_interests_profile_id_fkey', 'profile_interests', 'profile',
        ['profile_id'], ['id'], ondelete='CASCADE',
    )

    op.drop_constraint('profile_documents_profile_id_fkey', 'profile_documents', type_='foreignkey')
    op.create_foreign_key(
        'profile_documents_profile_id_fkey', 'profile_documents', 'profile',
        ['profile_id'], ['id'], ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('profile_documents_profile_id_fkey', 'profile_documents', type_='foreignkey')
    op.create_foreign_key('profile_documents_profile_id_fkey', 'profile_documents', 'profile', ['profile_id'], ['id'])

    op.drop_constraint('profile_interests_profile_id_fkey', 'profile_interests', type_='foreignkey')
    op.create_foreign_key('profile_interests_profile_id_fkey', 'profile_interests', 'profile', ['profile_id'], ['id'])

    op.drop_constraint('profile_commodities_profile_id_fkey', 'profile_commodities', type_='foreignkey')
    op.create_foreign_key('profile_commodities_profile_id_fkey', 'profile_commodities', 'profile', ['profile_id'], ['id'])
