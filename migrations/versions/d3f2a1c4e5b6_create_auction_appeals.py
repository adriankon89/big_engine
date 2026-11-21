"""create auction appeals

Revision ID: d3f2a1c4e5b6
Revises: c2d8e7f4a901
Create Date: 2026-11-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d3f2a1c4e5b6"
down_revision: str | Sequence[str] | None = "c2d8e7f4a901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


appeal_status_enum = sa.Enum(
    "open",
    "under_review",
    "approved",
    "rejected",
    "cancelled",
    name="appealstatus",
)
appeal_reason_code_enum = sa.Enum(
    "incorrect_details",
    "policy_violation",
    "duplicate_auction",
    "fraud_suspected",
    "other",
    name="appealreasoncode",
)


def upgrade() -> None:
    bind = op.get_bind()
    appeal_status_enum.create(bind, checkfirst=True)
    appeal_reason_code_enum.create(bind, checkfirst=True)

    op.create_table(
        "auction_appeals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("auction_id", sa.Integer(), nullable=False),
        sa.Column("status", appeal_status_enum, server_default="open", nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("reason_code", appeal_reason_code_enum, nullable=False),
        sa.Column("reviewer_id", sa.Integer(), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["auction_id"],
            ["auctions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
    )
    op.create_index("ix_auction_appeals_auction_id", "auction_appeals", ["auction_id"])
    op.create_index(
        "ix_auction_appeals_reviewer_id", "auction_appeals", ["reviewer_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_auction_appeals_reviewer_id", table_name="auction_appeals")
    op.drop_index("ix_auction_appeals_auction_id", table_name="auction_appeals")
    op.drop_table("auction_appeals")

    bind = op.get_bind()
    appeal_status_enum.drop(bind, checkfirst=True)
    appeal_reason_code_enum.drop(bind, checkfirst=True)
