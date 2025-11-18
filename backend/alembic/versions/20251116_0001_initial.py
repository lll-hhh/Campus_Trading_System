"""Initial schema with 34+ tables."""
from __future__ import annotations

from alembic import op
from sqlalchemy import orm

from apps.core.models import Base

# revision identifiers, used by Alembic.
revision = "20251116_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables defined in SQLAlchemy metadata."""

    bind = op.get_bind()
    session = orm.Session(bind=bind)
    Base.metadata.create_all(bind=bind)
    session.commit()


def downgrade() -> None:
    """Drop all tables."""

    bind = op.get_bind()
    session = orm.Session(bind=bind)
    Base.metadata.drop_all(bind=bind)
    session.commit()
