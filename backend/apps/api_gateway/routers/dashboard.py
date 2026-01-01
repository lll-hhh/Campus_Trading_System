"""Dashboard aggregation endpoints."""
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_db_session
from apps.core.models import Category, DailyStat, Item, SyncLog, User, Transaction

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_dashboard_stats(session: Session = Depends(get_db_session)) -> Dict[str, Any]:
    """Return comprehensive dashboard statistics."""
    from datetime import timedelta
    
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    seven_days_ago = now - timedelta(days=7)
    
    # 用户统计
    total_users = session.execute(select(func.count(User.id))).scalar() or 0
    
    # 活跃用户（最近7天）- 从user_activities表统计
    try:
        active_users = session.execute(text("""
            SELECT COUNT(DISTINCT user_id) 
            FROM user_activities 
            WHERE created_at >= :seven_days_ago
        """), {"seven_days_ago": seven_days_ago}).scalar() or 0
    except:
        active_users = 0
    
    # 商品统计
    total_items = session.execute(select(func.count(Item.id))).scalar() or 0
    available_items = session.execute(
        select(func.count(Item.id)).where(Item.status == 'available')
    ).scalar() or 0
    today_new_items = session.execute(
        select(func.count(Item.id)).where(Item.created_at >= today_start)
    ).scalar() or 0
    
    # 交易统计（最近7天）
    total_transactions = session.execute(select(func.count(Transaction.id))).scalar() or 0
    total_amount = session.execute(select(func.sum(Transaction.final_amount))).scalar() or 0
    
    # 最近7天的交易额
    recent_revenue = session.execute(text("""
        SELECT COALESCE(SUM(final_amount), 0) 
        FROM transactions 
        WHERE created_at >= :seven_days_ago 
        AND status = 'completed'
    """), {"seven_days_ago": seven_days_ago}).scalar() or 0
    
    today_completed = session.execute(
        select(func.count(Transaction.id)).where(
            Transaction.status == 'completed',
            Transaction.completed_at >= today_start
        )
    ).scalar() or 0
    
    # 交易统计（今日）
    today_trade_count = session.execute(text("""
        SELECT COUNT(*) 
        FROM transactions 
        WHERE created_at >= :today_start
        AND status = 'completed'
    """), {"today_start": today_start}).scalar() or 0
    
    # 咨询数量（今日）
    today_inquiry_count = session.execute(text("""
        SELECT COUNT(*) 
        FROM messages 
        WHERE created_at >= :today_start
    """), {"today_start": today_start}).scalar() or 0
    
    # 趋势计算（简化版：与上周对比）
    fourteen_days_ago = now - timedelta(days=14)
    
    # 上周交易数
    last_week_trades = session.execute(text("""
        SELECT COUNT(*) 
        FROM transactions 
        WHERE created_at >= :fourteen_days_ago 
        AND created_at < :seven_days_ago
        AND status = 'completed'
    """), {"fourteen_days_ago": fourteen_days_ago, "seven_days_ago": seven_days_ago}).scalar() or 1
    
    trade_trend = ((today_trade_count - last_week_trades) / max(1, last_week_trades)) * 100
    
    return {
        # 前端需要的关键指标
        "today_trade_count": today_trade_count,
        "today_inquiry_count": today_inquiry_count,
        "active_users": active_users,
        "total_revenue": float(recent_revenue),
        
        # 趋势数据
        "trade_trend": round(trade_trend, 1),
        "inquiry_trend": 0,
        "user_trend": 0,
        "revenue_trend": 0,
        
        # 原有数据
        "users": {
            "total": total_users,
        },
        "items": {
            "total": total_items,
            "available": available_items,
            "today_new": today_new_items,
        },
        "transactions": {
            "total": total_transactions,
            "total_amount": float(total_amount) if total_amount else 0,
            "today_completed": today_completed,
        }
    }


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
            "trade_count": stat.sync_success_count,
            "inquiry_count": stat.sync_conflict_count,
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
                "currency": "CNY",  # ✅ 硬编码默认值
                "status": item.status,
                "category": category.name if category else None,
                "created_at": item.created_at.isoformat() if isinstance(item.created_at, datetime) else None,
            }
        )
    return payload


@router.get("/system-logs")
def get_system_logs(limit: int = 10, session: Session = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """Return recent system logs for activity timeline."""

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
