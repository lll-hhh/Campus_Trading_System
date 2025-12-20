"""Annotated copy of `backend/apps/api_gateway/routers/dashboard.py` with per-line comments.
仅供阅读与答辩，不用于运行。
"""
"""Dashboard aggregation endpoints."""  # 注: 模块文档说明
from datetime import datetime  # 注: 获取当前时间用于统计
from typing import Any, Dict, List  # 注: 类型提示

from fastapi import APIRouter, Depends  # 注: FastAPI 路由与依赖注入
from sqlalchemy import func, select  # 注: SQL 函数与 select 构造器
from sqlalchemy.orm import Session  # 注: ORM Session 类型

from apps.api_gateway.dependencies import get_db_session  # 注: 依赖注入，获得 DB session
from apps.core.models import Category, DailyStat, Item, SyncLog, User, Transaction  # 注: ORM 模型

router = APIRouter(prefix="/dashboard", tags=["dashboard"])  # 注: 创建 Dashboard 路由器


@router.get("/stats")
def get_dashboard_stats(session: Session = Depends(get_db_session)) -> Dict[str, Any]:
    """Return comprehensive dashboard statistics."""  # 注: 返回仪表盘总体统计数据

    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)  # 注: 当日开始时间

    # 用户统计
    total_users = session.execute(select(func.count(User.id))).scalar() or 0  # 注: 统计用户总数

    # 商品统计
    total_items = session.execute(select(func.count(Item.id))).scalar() or 0  # 注: 商品总数
    available_items = session.execute(
        select(func.count(Item.id)).where(Item.status == 'available')
    ).scalar() or 0  # 注: 可用商品数量
    today_new_items = session.execute(
        select(func.count(Item.id)).where(Item.created_at >= today_start)
    ).scalar() or 0  # 注: 今日新增商品

    # 交易统计
    total_transactions = session.execute(select(func.count(Transaction.id))).scalar() or 0  # 注: 交易总数
    total_amount = session.execute(select(func.sum(Transaction.final_amount))).scalar() or 0  # 注: 交易总额
    today_completed = session.execute(
        select(func.count(Transaction.id)).where(
            Transaction.status == 'completed',
            Transaction.completed_at >= today_start
        )
    ).scalar() or 0  # 注: 今日完成交易数

    return {
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
    }  # 注: 返回聚合 JSON


@router.get("/daily-stats")
def get_daily_stats(limit: int = 7, session: Session = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """Return up to `limit` recent daily stats for charts."""  # 注: 返回最近若干天的统计数组

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
    ]  # 注: 映射为前端友好的字典列表


@router.get("/inventory")
def get_latest_inventory(limit: int = 8, session: Session = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """Surface the latest inventory listings for dashboard cards."""  # 注: 返回最近的 inventory 项用于卡片显示

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
                "currency": "CNY",  # 注: 默认货币硬编码
                "status": item.status,
                "category": category.name if category else None,
                "created_at": item.created_at.isoformat() if isinstance(item.created_at, datetime) else None,
            }
        )
    return payload  # 注: 返回最新商品摘要


@router.get("/sync-logs")
def get_sync_logs(limit: int = 10, session: Session = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """Return recent sync logs for activity timeline."""  # 注: 返回最近的同步日志

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
    ]  # 注: 映射为前端时间轴需要的结构
