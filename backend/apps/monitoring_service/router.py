"""Monitoring service router definitions."""
from fastapi import APIRouter
from sqlalchemy import select

from apps.core.database import db_manager
from apps.core.models import DailyStat

router = APIRouter(prefix="/monitor", tags=["monitor"])


@router.get("/daily-stats")
def daily_stats(limit: int = 7) -> list[dict[str, int | str]]:
    """Return the latest N days of sync statistics."""

    with db_manager.session_scope("mysql") as session:
        stats = (
            session.execute(
                select(DailyStat).order_by(DailyStat.stat_date.desc()).limit(limit)
            )
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
