"""Operational and governance models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class Report(BaseModel):
    """User-submitted report."""

    __tablename__ = "reports"

    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    target_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("items.id"))
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="pending")


class ModerationTask(BaseModel):
    """Moderation workflow item."""

    __tablename__ = "moderation_tasks"

    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="open")
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Blacklist(BaseModel):
    """Blacklist entries for users or devices."""

    __tablename__ = "blacklists"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class AuditLog(BaseModel):
    """Auditable user actions."""

    __tablename__ = "audit_logs"

    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[int] = mapped_column(nullable=False)
    metadata: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")


class ConfigItem(BaseModel):
    """Key-value configuration stored in DB."""

    __tablename__ = "config_items"
    __table_args__ = (UniqueConstraint("config_key", name="uq_config_key"),)

    config_key: Mapped[str] = mapped_column(String(150), nullable=False)
    config_value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
