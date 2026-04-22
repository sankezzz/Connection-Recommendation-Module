"""add_cascade_delete_on_user_fks

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-22

Drop and recreate every FK that points at users.id so that deleting
a user automatically cleans up all dependent rows.
groups.created_by becomes nullable + SET NULL (group is kept, creator cleared).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # profile.users_id → CASCADE
    op.drop_constraint('profile_users_id_fkey', 'profile', type_='foreignkey')
    op.create_foreign_key(
        'profile_users_id_fkey', 'profile', 'users', ['users_id'], ['id'],
        ondelete='CASCADE',
    )

    # user_embeddings.user_id → CASCADE
    op.drop_constraint('user_embeddings_user_id_fkey', 'user_embeddings', type_='foreignkey')
    op.create_foreign_key(
        'user_embeddings_user_id_fkey', 'user_embeddings', 'users', ['user_id'], ['id'],
        ondelete='CASCADE',
    )

    # news_engagement.user_id → CASCADE
    op.drop_constraint('news_engagement_user_id_fkey', 'news_engagement', type_='foreignkey')
    op.create_foreign_key(
        'news_engagement_user_id_fkey', 'news_engagement', 'users', ['user_id'], ['id'],
        ondelete='CASCADE',
    )

    # user_cluster_taste.user_id → CASCADE
    op.drop_constraint('user_cluster_taste_user_id_fkey', 'user_cluster_taste', type_='foreignkey')
    op.create_foreign_key(
        'user_cluster_taste_user_id_fkey', 'user_cluster_taste', 'users', ['user_id'], ['id'],
        ondelete='CASCADE',
    )

    # group_members.user_id → CASCADE
    op.drop_constraint('group_members_user_id_fkey', 'group_members', type_='foreignkey')
    op.create_foreign_key(
        'group_members_user_id_fkey', 'group_members', 'users', ['user_id'], ['id'],
        ondelete='CASCADE',
    )

    # groups.created_by → SET NULL (make nullable first)
    op.alter_column('groups', 'created_by', nullable=True)
    op.drop_constraint('groups_created_by_fkey', 'groups', type_='foreignkey')
    op.create_foreign_key(
        'groups_created_by_fkey', 'groups', 'users', ['created_by'], ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('groups_created_by_fkey', 'groups', type_='foreignkey')
    op.create_foreign_key('groups_created_by_fkey', 'groups', 'users', ['created_by'], ['id'])
    op.alter_column('groups', 'created_by', nullable=False)

    op.drop_constraint('group_members_user_id_fkey', 'group_members', type_='foreignkey')
    op.create_foreign_key('group_members_user_id_fkey', 'group_members', 'users', ['user_id'], ['id'])

    op.drop_constraint('user_cluster_taste_user_id_fkey', 'user_cluster_taste', type_='foreignkey')
    op.create_foreign_key('user_cluster_taste_user_id_fkey', 'user_cluster_taste', 'users', ['user_id'], ['id'])

    op.drop_constraint('news_engagement_user_id_fkey', 'news_engagement', type_='foreignkey')
    op.create_foreign_key('news_engagement_user_id_fkey', 'news_engagement', 'users', ['user_id'], ['id'])

    op.drop_constraint('user_embeddings_user_id_fkey', 'user_embeddings', type_='foreignkey')
    op.create_foreign_key('user_embeddings_user_id_fkey', 'user_embeddings', 'users', ['user_id'], ['id'])

    op.drop_constraint('profile_users_id_fkey', 'profile', type_='foreignkey')
    op.create_foreign_key('profile_users_id_fkey', 'profile', 'users', ['users_id'], ['id'])
