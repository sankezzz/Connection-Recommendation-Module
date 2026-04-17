"""create_connections_tables

Revision ID: d7e3f1a4c2b9
Revises: b5e7f9a2c3d1
Create Date: 2026-04-16 18:00:00.000000

Replaces the legacy integer-based user_connections / message_requests tables
(which referenced the old "Users" test table) with UUID-based versions that
reference the real users.id primary key.

Schema
------
user_connections
    follower_id   UUID PK FK → users.id  CASCADE
    following_id  UUID PK FK → users.id  CASCADE
    followed_at   TIMESTAMP WITH TZ

message_requests
    id            SERIAL PK
    sender_id     UUID FK → users.id  CASCADE
    receiver_id   UUID FK → users.id  CASCADE
    status        VARCHAR(20)  default 'pending'   (pending|accepted|declined)
    sent_at       TIMESTAMP WITH TZ
    acted_at      TIMESTAMP WITH TZ  nullable
    UNIQUE (sender_id, receiver_id)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d7e3f1a4c2b9"
down_revision: Union[str, None] = "b5e7f9a2c3d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop legacy integer-based tables if they exist (from old test setup)
    op.execute("DROP TABLE IF EXISTS user_connections CASCADE")
    op.execute("DROP TABLE IF EXISTS message_requests CASCADE")

    # ── user_connections (UUID, composite PK) ──────────────────────────────────
    op.create_table(
        "user_connections",
        sa.Column("follower_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("following_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "followed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(["follower_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["following_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("follower_id", "following_id"),
    )

    # Index — "who does this user follow?" query is the hot path
    op.create_index(
        "idx_user_connections_follower",
        "user_connections",
        ["follower_id"],
    )

    # ── message_requests ───────────────────────────────────────────────────────
    op.create_table(
        "message_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("receiver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("acted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["receiver_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sender_id", "receiver_id", name="uq_message_request"),
    )

    # Index — inbox query ("requests where receiver_id = me")
    op.create_index(
        "idx_message_requests_receiver",
        "message_requests",
        ["receiver_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_message_requests_receiver", table_name="message_requests")
    op.drop_table("message_requests")
    op.drop_index("idx_user_connections_follower", table_name="user_connections")
    op.drop_table("user_connections")
