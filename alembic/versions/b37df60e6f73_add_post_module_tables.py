"""add_post_module_tables

Revision ID: b37df60e6f73
Revises: ef6df3239d62
Create Date: 2026-04-17

Adds:
  post_categories  — seeded: 1=Market Update 2=Knowledge 3=Discussion 4=Deal/Requirement 5=Other
  posts
  post_views / post_likes / post_comments / post_shares / post_saves
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b37df60e6f73'
down_revision: Union[str, None] = 'ef6df3239d62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    from sqlalchemy import inspect as sa_inspect
    existing = sa_inspect(bind).get_table_names()

    if 'post_categories' not in existing:
        op.create_table(
            'post_categories',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name'),
        )

    # Seed regardless — ON CONFLICT DO NOTHING is idempotent
    op.execute(
        "INSERT INTO post_categories (id, name) VALUES "
        "(1, 'Market Update'), "
        "(2, 'Knowledge'), "
        "(3, 'Discussion'), "
        "(4, 'Deal/Requirement'), "
        "(5, 'Other') "
        "ON CONFLICT DO NOTHING"
    )

    if 'posts' not in existing:
        op.create_table(
            'posts',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('profile_id', sa.Integer(), nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=False),
            sa.Column('commodity_id', sa.Integer(), nullable=False),
            sa.Column('image_url', sa.String(), nullable=True),
            sa.Column('caption', sa.Text(), nullable=False),
            sa.Column('is_public', sa.Boolean(), nullable=False),
            sa.Column('target_roles', sa.ARRAY(sa.Integer()), nullable=True),
            sa.Column('allow_comments', sa.Boolean(), nullable=False),
            sa.Column('grain_type_size', sa.String(length=100), nullable=True),
            sa.Column('commodity_quantity', sa.Float(), nullable=True),
            sa.Column('price_type', sa.String(length=20), nullable=True),
            sa.Column('other_description', sa.Text(), nullable=True),
            sa.Column('like_count', sa.Integer(), nullable=False),
            sa.Column('view_count', sa.Integer(), nullable=False),
            sa.Column('comment_count', sa.Integer(), nullable=False),
            sa.Column('share_count', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['category_id'], ['post_categories.id']),
            sa.ForeignKeyConstraint(['commodity_id'], ['commodities.id']),
            sa.ForeignKeyConstraint(['profile_id'], ['profile.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'post_views' not in existing:
        op.create_table(
            'post_views',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('post_id', sa.Integer(), nullable=False),
            sa.Column('profile_id', sa.Integer(), nullable=False),
            sa.Column('viewed_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['profile_id'], ['profile.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('post_id', 'profile_id', name='uq_post_view'),
        )

    if 'post_likes' not in existing:
        op.create_table(
            'post_likes',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('post_id', sa.Integer(), nullable=False),
            sa.Column('profile_id', sa.Integer(), nullable=False),
            sa.Column('liked_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['profile_id'], ['profile.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('post_id', 'profile_id', name='uq_post_like'),
        )

    if 'post_comments' not in existing:
        op.create_table(
            'post_comments',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('post_id', sa.Integer(), nullable=False),
            sa.Column('profile_id', sa.Integer(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['profile_id'], ['profile.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'post_shares' not in existing:
        op.create_table(
            'post_shares',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('post_id', sa.Integer(), nullable=False),
            sa.Column('profile_id', sa.Integer(), nullable=False),
            sa.Column('shared_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['profile_id'], ['profile.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'post_saves' not in existing:
        op.create_table(
            'post_saves',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('post_id', sa.Integer(), nullable=False),
            sa.Column('profile_id', sa.Integer(), nullable=False),
            sa.Column('saved_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['profile_id'], ['profile.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('post_id', 'profile_id', name='uq_post_save'),
        )


def downgrade() -> None:
    op.drop_table('post_saves')
    op.drop_table('post_shares')
    op.drop_table('post_comments')
    op.drop_table('post_likes')
    op.drop_table('post_views')
    op.drop_table('posts')
    op.drop_table('post_categories')
