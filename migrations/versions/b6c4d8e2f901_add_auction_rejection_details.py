"""add auction rejection details

Revision ID: b6c4d8e2f901
Revises: f1a2b3c4d5e6
Create Date: 2026-10-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b6c4d8e2f901"
down_revision: str | Sequence[str] | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


rejection_source_enum = sa.Enum("USER", "AI", name="rejectionsource")


def upgrade() -> None:
    bind = op.get_bind()
    rejection_source_enum.create(bind, checkfirst=True)
    with op.batch_alter_table("auctions") as batch_op:
        batch_op.add_column(sa.Column("rejection_reason", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("rejection_source", rejection_source_enum, nullable=True)
        )
        batch_op.add_column(sa.Column("rejected_by_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_auctions_rejected_by_id_users", "users", ["rejected_by_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("auctions") as batch_op:
        batch_op.drop_constraint("fk_auctions_rejected_by_id_users", type_="foreignkey")
        batch_op.drop_column("rejected_by_id")
        batch_op.drop_column("rejection_source")
        batch_op.drop_column("rejection_reason")
    rejection_source_enum.drop(op.get_bind(), checkfirst=True)
