"""add auction moderator assignment

Revision ID: c2d8e7f4a901
Revises: b6c4d8e2f901
Create Date: 2026-10-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c2d8e7f4a901"
down_revision: str | Sequence[str] | None = "b6c4d8e2f901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("auctions") as batch_op:
        batch_op.add_column(sa.Column("moderator_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_auctions_moderator_id_users", "users", ["moderator_id"], ["id"]
        )
    op.create_index("ix_auctions_moderator_id", "auctions", ["moderator_id"])

    op.create_table(
        "moderator_assignment_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("last_moderator_id", sa.Integer(), nullable=True),
    )
    op.bulk_insert(
        sa.table(
            "moderator_assignment_state",
            sa.column("id", sa.Integer()),
            sa.column("last_moderator_id", sa.Integer()),
        ),
        [{"id": 1, "last_moderator_id": None}],
    )

    op.execute(
        sa.text(
            "UPDATE auctions "
            "SET moderator_id = ("
            "SELECT id FROM users "
            "WHERE role IN ('admin', 'moderator') AND status = 'active' "
            "AND users.id != auctions.seller_id "
            "ORDER BY id LIMIT 1"
            ")"
        )
    )
    op.execute(
        sa.text(
            "UPDATE moderator_assignment_state "
            "SET last_moderator_id = ("
            "SELECT moderator_id FROM auctions "
            "WHERE moderator_id IS NOT NULL "
            "ORDER BY id DESC LIMIT 1"
            ") WHERE id = 1"
        )
    )


def downgrade() -> None:
    op.drop_table("moderator_assignment_state")
    op.drop_index("ix_auctions_moderator_id", table_name="auctions")
    with op.batch_alter_table("auctions") as batch_op:
        batch_op.drop_constraint("fk_auctions_moderator_id_users", type_="foreignkey")
        batch_op.drop_column("moderator_id")
