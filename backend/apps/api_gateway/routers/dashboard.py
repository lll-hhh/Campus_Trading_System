"""Dashboard aggregation endpoints."""
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_db_session
from apps.core.models import Category, DailyStat, Item, SyncLog

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/daily-stats")
def get_daily_stats(limit: int = 7, session: Session = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """Return up to `limit` recent daily stats for charts."""

    stats = (
        session.execute(select(DailyStat).order_by(DailyStat.stat_date.desc()).limit(limit))
        .scalars()
        .all()
    )
    return [
        {
            "date": stat.stat_date.isoformat(),
            "sync_success": stat.sync_success_count,
            "sync_conflicts": stat.sync_conflict_count,
            "ai_requests": stat.ai_request_count,
            "inventory_changes": stat.inventory_changes,
        }
        for stat in stats
    ]


@router.get("/inventory")
def get_latest_inventory(limit: int = 8, session: Session = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """Surface the latest inventory listings for dashboard cards."""

    items = (
        session.execute(
            select(Item, Category)
            .join(Category, Item.category_id == Category.id)
            .order_by(Item.created_at.desc())
            .limit(limit)
        )
        .all()
    )
    payload: List[Dict[str, Any]] = []
    for item, category in items:
        payload.append(
            {
                "id": item.id,
                "title": item.title,
                "price": float(item.price),
                "currency": item.currency,
                "status": item.status,
                "category": category.name if category else None,
                "created_at": item.created_at.isoformat() if isinstance(item.created_at, datetime) else None,
            }
        )
    return payload


@router.get("/sync-logs")
def get_sync_logs(limit: int = 10, session: Session = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """Return recent sync logs for activity timeline."""

    logs = (
        session.execute(select(SyncLog).order_by(SyncLog.started_at.desc()).limit(limit))
        .scalars()
        .all()
    )
    return [
        {
            "id": log.id,
            "config_id": log.config_id,
            "status": log.status,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
        }
        for log in logs
    ]
