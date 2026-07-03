"""user display name

Adds the nullable ``display_name`` column to the ``users`` table, backing the
optional friendly name shown in the UI instead of the email. The migration is
purely additive: the column is nullable, so existing accounts stay valid and the
email remains the display fallback. Mirrors the ``User`` model in ``db/models.py``.

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-03

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the nullable ``display_name`` column to ``users``."""
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("display_name", sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Drop the ``display_name`` column from ``users``."""
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("display_name")
