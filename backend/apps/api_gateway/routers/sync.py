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
    _: User = Depends(require_roles("market_admin", "trader")),
) -> Dict[str, Any]:
    """Return sync runtime status, configs, and counters."""

    configs = session.execute(select(SyncConfig)).scalars().all()
    last_log = (
        session.execute(select(SyncLog).order_by(SyncLog.started_at.desc())).scalars().first()
    )
    conflict_count = session.scalar(
        select(func.count()).where(ConflictRecord.status == "pending")
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


@router.get("/conflicts")
def list_conflicts(
    session: Session = Depends(get_db_session),
    _: User = Depends(require_roles("market_admin")),
) -> List[Dict[str, Any]]:
    """Return the latest pending conflict records for the UI."""

    conflicts = (
        session.execute(
            select(ConflictRecord)
            .where(ConflictRecord.status == "pending")
            .order_by(ConflictRecord.created_at.desc())
            .limit(20)
        )
        .scalars()
        .all()
    )

    return [
        {
            "id": conflict.id,
            "table": conflict.table_name,
            "record_id": conflict.record_id,
            "source": conflict.source,
            "target": conflict.target,
            "created_at": conflict.created_at.isoformat(),
        }
        for conflict in conflicts
    ]


@router.post("/run")
def trigger_manual_sync(_: User = Depends(require_roles("market_admin"))) -> Dict[str, str]:
    """Allow admin to trigger sync without visiting sync service."""

    sync_engine.run_periodic_sync()
    return {"status": "scheduled"}


class ConflictResolutionPayload(BaseModel):
    """Payload for resolving conflicts."""

    strategy: Literal["source", "target", "manual"]
    note: str | None = None


@router.post("/conflicts/{conflict_id}/resolve")
def resolve_conflict(
    conflict_id: int,
    payload: ConflictResolutionPayload,
    admin: User = Depends(require_roles("market_admin")),
) -> Dict[str, str]:
    """Resolve a conflict by applying the chosen strategy."""

    with db_manager.session_scope("mysql") as session:
        conflict = session.get(ConflictRecord, conflict_id)
        if conflict is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conflict not found")
        if conflict.status != "pending":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conflict handled")

        if payload.strategy in {"source", "target"}:
            statement = conflict.payload.get("statement")
            params = decode_params(conflict.payload.get("params", {}))
            if statement:
                target_db = conflict.target if payload.strategy == "source" else conflict.source
                with db_manager.session_scope(target_db) as peer_session:
                    peer_session.execute(text(statement), params)

        conflict.status = "resolved"
        conflict.resolved_by = admin.id
        conflict.resolved_at = datetime.utcnow()
        conflict.resolution_note = payload.note or f"strategy={payload.strategy}"
        session.add(conflict)

    return {"status": "resolved"}
