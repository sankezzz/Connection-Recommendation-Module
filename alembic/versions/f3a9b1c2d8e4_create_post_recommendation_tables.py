"""create_post_recommendation_tables

Revision ID: f3a9b1c2d8e4
Revises: 33c3b84cc751
Create Date: 2026-04-17

New tables
----------
post_embeddings     – 11-dim vector per post, partition label, expiry metadata
popular_posts       – velocity-scored posts per commodity (recomputed every 15 min)
user_taste_profiles – raw interaction counts per category per user
seen_posts          – which posts a user has already been served (TTL 30 days)

Modified tables
---------------
posts               – add save_count INTEGER NOT NULL DEFAULT 0
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'f3a9b1c2d8e4'
down_revision: Union[str, None] = '33c3b84cc751'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # posts: add save_count
    # ------------------------------------------------------------------
    op.add_column(
        'posts',
        sa.Column('save_count', sa.Integer(), nullable=False, server_default='0'),
    )

    # ------------------------------------------------------------------
    # post_embeddings
    # ------------------------------------------------------------------
    op.create_table(
        'post_embeddings',
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('vector', sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column('partition', sa.String(length=10), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('category', sa.String(length=30), nullable=False),
        sa.Column('commodity_idx', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('post_id'),
    )
    op.create_index('ix_post_embeddings_partition_active', 'post_embeddings',
                    ['partition', 'is_active'])
    op.create_index('ix_post_embeddings_created_at', 'post_embeddings', ['created_at'])

    # ------------------------------------------------------------------
    # popular_posts
    # ------------------------------------------------------------------
    op.create_table(
        'popular_posts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('commodity_idx', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=30), nullable=False),
        sa.Column('velocity_score', sa.Float(), nullable=False),
        sa.Column('saves_count', sa.Integer(), nullable=False),
        sa.Column('likes_count', sa.Integer(), nullable=False),
        sa.Column('comments_count', sa.Integer(), nullable=False),
        sa.Column('hours_since_post', sa.Float(), nullable=False),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('post_id', name='uq_popular_post_id'),
    )
    op.create_index('ix_popular_posts_commodity_idx', 'popular_posts', ['commodity_idx'])
    op.create_index('ix_popular_posts_velocity', 'popular_posts',
                    ['commodity_idx', 'is_active', 'velocity_score'])

    # ------------------------------------------------------------------
    # user_taste_profiles
    # ------------------------------------------------------------------
    op.create_table(
        'user_taste_profiles',
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('market_update_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('deal_req_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('discussion_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('knowledge_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('other_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_events', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['profile.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('profile_id'),
    )

    # ------------------------------------------------------------------
    # seen_posts
    # ------------------------------------------------------------------
    op.create_table(
        'seen_posts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['profile_id'], ['profile.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('profile_id', 'post_id', name='uq_seen_post'),
    )
    op.create_index('ix_seen_posts_profile_seen_at', 'seen_posts', ['profile_id', 'seen_at'])


def downgrade() -> None:
    op.drop_table('seen_posts')
    op.drop_table('user_taste_profiles')
    op.drop_table('popular_posts')
    op.drop_table('post_embeddings')
    op.drop_column('posts', 'save_count')
