"""create_profile_module_tables

Revision ID: ef6df3239d62
Revises:
Create Date: 2026-04-16 12:11:21.889060

Schema
------
users           — UUID PK (held in JWT before row exists)
roles           — int PK, seeded: 1=Trader 2=Broker 3=Exporter
commodities     — int PK, seeded: 1=Rice 2=Cotton 3=Sugar
interests       — int PK, seeded: 1=Connections 2=Leads 3=News
profile         — int PK autoincrement, FK → users / roles
profile_commodities — junction (profile ↔ commodity)
profile_interests   — junction (profile ↔ interest)
profile_documents   — optional verification docs per profile
posts           — int PK autoincrement, FK → profile
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'ef6df3239d62'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('country_code', sa.String(length=5), nullable=False),
        sa.Column('phone_number', sa.String(length=15), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('fcm_token', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('country_code', 'phone_number', name='uq_phone'),
    )

    # ------------------------------------------------------------------
    # lookup tables (fixed int IDs — seeded below)
    # ------------------------------------------------------------------
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table(
        'commodities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table(
        'interests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # ------------------------------------------------------------------
    # seed lookup tables
    # ------------------------------------------------------------------
    op.execute(
        "INSERT INTO roles (id, name, description) VALUES "
        "(1, 'Trader',   'Trades commodities in domestic markets.'), "
        "(2, 'Broker',   'Connects buyers and sellers.'), "
        "(3, 'Exporter', 'Supplies commodities to global markets.')"
    )

    op.execute(
        "INSERT INTO commodities (id, name) VALUES "
        "(1, 'Rice'), (2, 'Cotton'), (3, 'Sugar')"
    )

    op.execute(
        "INSERT INTO interests (id, name) VALUES "
        "(1, 'Connections'), (2, 'Leads'), (3, 'News')"
    )

    # ------------------------------------------------------------------
    # profile
    # ------------------------------------------------------------------
    op.create_table(
        'profile',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('users_id', sa.UUID(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('business_name', sa.String(length=100), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('quantity_min', sa.Numeric(), nullable=False),
        sa.Column('quantity_max', sa.Numeric(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('is_user_verified', sa.Boolean(), nullable=False),
        sa.Column('is_business_verified', sa.Boolean(), nullable=False),
        sa.Column('followers_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
        sa.ForeignKeyConstraint(['users_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('users_id'),
    )

    # ------------------------------------------------------------------
    # junction tables
    # ------------------------------------------------------------------
    op.create_table(
        'profile_commodities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('commodity_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['commodity_id'], ['commodities.id']),
        sa.ForeignKeyConstraint(['profile_id'], ['profile.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('profile_id', 'commodity_id', name='uq_profile_commodity'),
    )

    op.create_table(
        'profile_interests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('interest_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['interest_id'], ['interests.id']),
        sa.ForeignKeyConstraint(['profile_id'], ['profile.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('profile_id', 'interest_id', name='uq_profile_interest'),
    )

    # ------------------------------------------------------------------
    # profile_documents (optional verification, screen 6)
    # document_type: pan_card | aadhaar_card | gst_certificate | trade_license
    # ------------------------------------------------------------------
    op.create_table(
        'profile_documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('document_type', sa.String(length=30), nullable=False),
        sa.Column('document_number', sa.String(length=100), nullable=False),
        sa.Column('verification_status', sa.String(length=20), nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['profile_id'], ['profile.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # ------------------------------------------------------------------
    # posts
    # ------------------------------------------------------------------
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['profile.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('posts')
    op.drop_table('profile_documents')
    op.drop_table('profile_interests')
    op.drop_table('profile_commodities')
    op.drop_table('profile')
    op.drop_table('interests')
    op.drop_table('commodities')
    op.drop_table('roles')
    op.drop_table('users')
