"""Synchronization and monitoring tables."""
from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class SyncConfig(BaseModel):
    """Configuration for cross-database sync."""

    __tablename__ = "sync_configs"

    source: Mapped[str] = mapped_column(String(64), nullable=False)
    target: Mapped[str] = mapped_column(String(64), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, server_default="realtime")
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, server_default="300")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class SyncLog(BaseModel):
    """Logs for executed sync jobs."""

    __tablename__ = "sync_logs"

    config_id: Mapped[int] = mapped_column(ForeignKey("sync_configs.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    stats: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}", default=dict)


class ConflictRecord(BaseModel):
    """Detected conflicts during sync."""

    __tablename__ = "conflict_records"

    table_name: Mapped[str] = mapped_column(String(128), nullable=False)
    record_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    target: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="pending")
    resolved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolution_note: Mapped[Optional[str]] = mapped_column(String(255))
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)


class DailyStat(BaseModel):
    """Aggregated daily statistics for dashboards."""

    __tablename__ = "daily_stats"

    stat_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    sync_success_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0", default=0
    )
    sync_conflict_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0", default=0
    )
    ai_request_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0", default=0
    )
    inventory_changes: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0", default=0
    )
