"""Initial schema with 34+ tables.

Note: This migration relies on all tables being created automatically
via SQLAlchemy metadata.create_all at startup when tables don't exist yet.
We use a simple pass here so Alembic can mark it as applied.
"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251116_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op: tables are created by SQLAlchemy metadata at startup."""
    pass


def downgrade() -> None:
    """No-op: handle drops manually if needed."""
    pass
