"""feedback table

Adds the ``feedback`` table backing a student's thumbs up/down on a tutor
answer. A feedback row captures the rating (``1`` up, ``-1`` down), an optional
note, and the verbatim question/answer text so it is self-contained for later
evaluation. This table is additive and independent of the existing tables: it
does not modify any of them, so the migration is non-breaking. Mirrors the
``Feedback`` model in ``db/models.py``.

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-25

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the ``feedback`` table and its ``student_id`` index."""
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("feedback", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_feedback_student_id"), ["student_id"], unique=False)


def downgrade() -> None:
    """Drop the ``feedback`` table and its index."""
    with op.batch_alter_table("feedback", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_feedback_student_id"))
    op.drop_table("feedback")
