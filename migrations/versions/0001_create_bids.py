"""create bids table

Revision ID: 0001_create_bids
Revises:
Create Date: 2026-09-19
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_create_bids"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bids",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("bids")
