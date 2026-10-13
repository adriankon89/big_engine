"""add original filename to auction images

Revision ID: f1a2b3c4d5e6
Revises: e0005587b220
Create Date: 2026-10-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: str | Sequence[str] | None = "5798d7e2d3c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "auction_images",
        sa.Column("original_filename", sa.String(length=500), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE auction_images "
            "SET original_filename = storage_key "
            "WHERE original_filename IS NULL"
        )
    )
    op.alter_column(
        "auction_images",
        "original_filename",
        existing_type=sa.String(length=500),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("auction_images", "original_filename")
