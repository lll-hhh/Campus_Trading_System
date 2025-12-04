"""Sync routing layer for admin endpoints."""
from datetime import datetime
from typing import Any, Dict, List, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import (
    get_current_settings,
    get_db_session,
    require_roles,
)
from apps.core.database import db_manager
from apps.core.models import ConflictRecord, DailyStat, SyncConfig, SyncLog, User
from apps.core.sync_engine import sync_engine
from apps.core.sync_payloads import decode_params

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/status")
def get_sync_status(
    settings=Depends(get_current_settings),
    session: Session = Depends(get_db_session),
    _: User = Depends(require_roles("admin", "market_admin", "trader")),
) -> Dict[str, Any]:
    """Return sync runtime status, configs, and counters."""

    configs = session.execute(select(SyncConfig)).scalars().all()
    last_log = (
        session.execute(select(SyncLog).order_by(SyncLog.started_at.desc())).scalars().first()
    )
    conflict_count = session.scalar(
        text("SELECT COUNT(*) FROM conflict_records WHERE resolved = 0")
    ) or 0
    today_stat = (
        session.execute(select(DailyStat).order_by(DailyStat.stat_date.desc())).scalars().first()
    )

    return {
        "targets": list({cfg.target for cfg in configs}) or ["mysql"],
        "mode": "+".join(sorted({cfg.mode for cfg in configs})) if configs else "realtime",
        "environment": settings.environment,
        "conflicts": conflict_count,
        "last_run": last_log.started_at.isoformat() if last_log else None,
        "daily_stat": {
            "date": today_stat.stat_date.isoformat() if today_stat else None,
            "sync_success": today_stat.sync_success_count if today_stat else 0,
            "sync_conflicts": today_stat.sync_conflict_count if today_stat else 0,
        },
    }


@router.post("/run")
def trigger_manual_sync(_: User = Depends(require_roles("admin", "market_admin"))) -> Dict[str, str]:
    """Allow admin to trigger sync without visiting sync service."""

    sync_engine.run_periodic_sync()
    return {"status": "scheduled"}
