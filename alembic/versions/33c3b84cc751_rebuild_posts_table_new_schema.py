"""rebuild_posts_table_new_schema

Revision ID: 33c3b84cc751
Revises: b37df60e6f73
Create Date: 2026-04-17 12:38:06.131150

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '33c3b84cc751'
down_revision: Union[str, None] = 'b37df60e6f73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old posts — CASCADE removes FK constraints from interaction tables
    op.execute('DROP TABLE posts CASCADE')

    # Recreate posts with current schema
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

    # Restore FK constraints on interaction tables (they were dropped by CASCADE)
    op.create_foreign_key('fk_post_views_post_id',    'post_views',    'posts', ['post_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_post_likes_post_id',    'post_likes',    'posts', ['post_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_post_comments_post_id', 'post_comments', 'posts', ['post_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_post_shares_post_id',   'post_shares',   'posts', ['post_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_post_saves_post_id',    'post_saves',    'posts', ['post_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    op.drop_constraint('fk_post_saves_post_id',    'post_saves',    type_='foreignkey')
    op.drop_constraint('fk_post_shares_post_id',   'post_shares',   type_='foreignkey')
    op.drop_constraint('fk_post_comments_post_id', 'post_comments', type_='foreignkey')
    op.drop_constraint('fk_post_likes_post_id',    'post_likes',    type_='foreignkey')
    op.drop_constraint('fk_post_views_post_id',    'post_views',    type_='foreignkey')

    op.drop_table('posts')

    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['profile.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
