"""create_groups_tables

Revision ID: 3f8a2c1d9e74
Revises: ef6df3239d62
Create Date: 2026-04-16 16:00:00.000000

New tables
----------
groups              — core group record (JSONB commodity + target_roles)
group_members       — composite PK (group_id, user_id)
group_activity_cache — denormalised activity counters (updated by cron)
group_embeddings    — 11-dim IS vector stored as JSONB list[float]
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "3f8a2c1d9e74"
down_revision: Union[str, None] = "ef6df3239d62"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # groups
    # ------------------------------------------------------------------
    op.create_table(
        "groups",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("group_rules", sa.Text(), nullable=True),
        sa.Column("icon_url", sa.String(length=500), nullable=True),
        # JSONB arrays — e.g. ["sugar","rice"] / ["trader","broker"]
        sa.Column("commodity", postgresql.JSONB(), nullable=True),
        sa.Column("target_roles", postgresql.JSONB(), nullable=True),
        sa.Column("region_lat", sa.Float(), nullable=True),
        sa.Column("region_lon", sa.Float(), nullable=True),
        sa.Column("region_market", sa.String(length=200), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=True),
        # public | private | invite_only
        sa.Column("accessibility", sa.String(length=20), nullable=False, server_default="public"),
        # all_members | admins_only
        sa.Column("posting_perm", sa.String(length=20), nullable=False, server_default="all_members"),
        sa.Column("chat_perm", sa.String(length=20), nullable=False, server_default="all_members"),
        sa.Column("invite_link_token", sa.String(length=100), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("member_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invite_link_token"),
    )

    # ------------------------------------------------------------------
    # group_members   composite PK (group_id, user_id)
    # ------------------------------------------------------------------
    op.create_table(
        "group_members",
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        # admin | member
        sa.Column("role", sa.String(length=20), nullable=False, server_default="member"),
        sa.Column("is_frozen", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_muted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("group_id", "user_id"),
    )

    # Index — fast lookup of all groups a user belongs to
    op.create_index("idx_group_members_user", "group_members", ["user_id"])

    # ------------------------------------------------------------------
    # group_activity_cache   updated by background cron every 15 min
    # ------------------------------------------------------------------
    op.create_table(
        "group_activity_cache",
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("messages_24h", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unique_senders_24h", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_members_7d", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("member_growth_7d", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("group_id"),
    )

    # ------------------------------------------------------------------
    # group_embeddings   11-dim IS vector stored as JSONB list[float]
    # Layout: [3 commodity | 3 role | 3 geo | 2 zeros]
    # ------------------------------------------------------------------
    op.create_table(
        "group_embeddings",
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("embedding", postgresql.JSONB(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("group_id"),
    )


def downgrade() -> None:
    op.drop_table("group_embeddings")
    op.drop_index("idx_group_members_user", table_name="group_members")
    op.drop_table("group_activity_cache")
    op.drop_table("group_members")
    op.drop_table("groups")
