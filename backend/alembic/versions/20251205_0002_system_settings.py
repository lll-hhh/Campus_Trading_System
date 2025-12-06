"""Add system_settings table for admin runtime configuration."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251205_0002"
down_revision = "20251116_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_settings",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
    sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("sync_version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], name="fk_system_settings_updated_by_users"),
        sa.UniqueConstraint("category", "key", name="uq_system_settings_category_key"),
    )
    op.create_index("ix_system_settings_category", "system_settings", ["category"])


def downgrade() -> None:
    op.drop_index("ix_system_settings_category", table_name="system_settings")
    op.drop_table("system_settings")
