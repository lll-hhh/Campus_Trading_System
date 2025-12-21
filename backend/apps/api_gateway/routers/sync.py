"""Sync routing layer for admin endpoints."""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import (
    get_current_settings,
    get_db_session,
    require_roles,
)
from apps.core.models import ConflictRecord, DailyStat, SyncConfig, SyncLog, User
from apps.core.sync_engine import sync_engine

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


class ResolveConflictRequest(BaseModel):
    strategy: str  # 'source', 'target', 'manual'


@router.put("/conflicts/{conflict_id}/resolve")
def resolve_conflict(
    conflict_id: int,
    request: ResolveConflictRequest,
    session: Session = Depends(get_db_session),
    _: User = Depends(require_roles("admin")),
) -> Dict[str, Any]:
    """解决冲突记录"""
    conflict = session.get(ConflictRecord, conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="冲突记录不存在")
    
    # 标记为已解决
    stmt = (
        update(ConflictRecord)
        .where(ConflictRecord.id == conflict_id)
        .values(resolved=True, resolved_at=text("NOW()"))
    )
    session.execute(stmt)
    session.commit()
    
    return {"message": "冲突已解决", "conflict_id": conflict_id, "strategy": request.strategy}
