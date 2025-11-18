"""Sync service router definitions."""
from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import func, select

from apps.core.database import db_manager
from apps.core.models import ConflictRecord, SyncConfig, SyncLog
from apps.core.sync_engine import sync_engine

router = APIRouter(prefix="/sync-service", tags=["sync-service"])


@router.get("/metrics")
def get_metrics() -> dict[str, int]:
    """Return live sync metrics from the database."""

    with db_manager.session_scope("mysql") as session:
        pending_jobs = session.scalar(
            select(func.count()).select_from(SyncConfig).where(SyncConfig.enabled.is_(True))
        )
        conflict_count = session.scalar(
            select(func.count()).select_from(ConflictRecord).where(ConflictRecord.status == "pending")
        )
        last_run = session.execute(
            select(SyncLog.started_at).order_by(SyncLog.started_at.desc())
        ).scalar_one_or_none()

    return {
        "pending_jobs": pending_jobs or 0,
        "conflicts": conflict_count or 0,
        "last_run": last_run.isoformat() if isinstance(last_run, datetime) else None,
    }


@router.post("/run")
def trigger_sync() -> dict[str, str]:
    """Trigger a manual periodic sync run."""

    sync_engine.run_periodic_sync()
    return {"status": "scheduled"}
