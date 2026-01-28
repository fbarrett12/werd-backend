"""word difficulty is computed from attempts

Revision ID: 892eecf6fa53
Revises: 238b6ca2a913
Create Date: 2026-01-28 00:53:15.393302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '892eecf6fa53'
down_revision: Union[str, Sequence[str], None] = '238b6ca2a913'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
   # Add counters with server defaults, initially nullable
    op.add_column(
        "words",
        sa.Column("times_seen", sa.Integer(), nullable=True, server_default=sa.text("0")),
    )
    op.add_column(
        "words",
        sa.Column("times_correct", sa.Integer(), nullable=True, server_default=sa.text("0")),
    )
    op.add_column(
        "words",
        sa.Column("times_incorrect", sa.Integer(), nullable=True, server_default=sa.text("0")),
    )

    # Backfill existing rows
    op.execute("UPDATE words SET times_seen = 0 WHERE times_seen IS NULL")
    op.execute("UPDATE words SET times_correct = 0 WHERE times_correct IS NULL")
    op.execute("UPDATE words SET times_incorrect = 0 WHERE times_incorrect IS NULL")

    # Enforce NOT NULL after backfill
    op.alter_column("words", "times_seen", nullable=False)
    op.alter_column("words", "times_correct", nullable=False)
    op.alter_column("words", "times_incorrect", nullable=False)

    # Difficulty: enforce default + non-null
    op.execute("UPDATE words SET difficulty = 1 WHERE difficulty IS NULL")
    op.alter_column("words", "difficulty", server_default=sa.text("1"))
    op.alter_column("words", "difficulty", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Revert difficulty constraints
    op.alter_column("words", "difficulty", nullable=True)
    op.alter_column("words", "difficulty", server_default=None)

    # Drop counters
    op.drop_column("words", "times_incorrect")
    op.drop_column("words", "times_correct")
    op.drop_column("words", "times_seen")
