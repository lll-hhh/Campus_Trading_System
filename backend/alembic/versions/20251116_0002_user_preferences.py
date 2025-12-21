"""Add user preferences table for privacy/notification settings."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251116_0002"
down_revision = "20251116_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.Column("sync_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("show_email", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("show_phone", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("allow_follow", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("allow_message", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("email_notification", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("message_notification", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("transaction_notification", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("comment_notification", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("system_notification", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_table("user_preferences")
