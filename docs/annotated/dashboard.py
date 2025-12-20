"""Annotated copy of `backend/apps/api_gateway/routers/dashboard.py` with per-line comments.
此文件为只读注释版，供 PPT/报告阅读，不用于运行。
"""
from datetime import datetime  # 注: 导入 datetime 类用于时间处理
from typing import Any, Dict, List  # 注: 导入类型提示工具

from fastapi import APIRouter, Depends  # 注: 导入 FastAPI 路由和依赖注入
from sqlalchemy import func, select  # 注: 导入 SQLAlchemy 查询构建函数
from sqlalchemy.orm import Session  # 注: 导入 Session 类型提示

from apps.api_gateway.dependencies import get_db_session  # 注: 导入获取数据库会话的依赖
from apps.core.models import Category, DailyStat, Item, SyncLog, User, Transaction  # 注: 导入相关数据模型

router = APIRouter(prefix="/dashboard", tags=["dashboard"])  # 注: 创建路由组，前缀为 /dashboard


@router.get("/stats")  # 注: 定义 GET /stats 接口
def get_dashboard_stats(session: Session = Depends(get_db_session)) -> Dict[str, Any]:  # 注: 获取仪表盘核心统计数据
    """Return comprehensive dashboard statistics."""
    
    now = datetime.now()  # 注: 获取当前时间
    today_start = datetime(now.year, now.month, now.day)  # 注: 计算今日起始时间 (00:00:00)
    
    # 用户统计
    total_users = session.execute(select(func.count(User.id))).scalar() or 0  # 注: 查询用户总数
    
    # 商品统计
    total_items = session.execute(select(func.count(Item.id))).scalar() or 0  # 注: 查询商品总数
    available_items = session.execute(  # 注: 查询在售商品数
        select(func.count(Item.id)).where(Item.status == 'available')
    ).scalar() or 0
    today_new_items = session.execute(  # 注: 查询今日新增商品数
        select(func.count(Item.id)).where(Item.created_at >= today_start)
    ).scalar() or 0
    
    # 交易统计
    total_transactions = session.execute(select(func.count(Transaction.id))).scalar() or 0  # 注: 查询交易总数
    total_amount = session.execute(select(func.sum(Transaction.final_amount))).scalar() or 0  # 注: 查询交易总金额
    today_completed = session.execute(  # 注: 查询今日完成的交易数
        select(func.count(Transaction.id)).where(
            Transaction.status == 'completed',
            Transaction.completed_at >= today_start
        )
    ).scalar() or 0
    
    return {  # 注: 返回结构化统计数据
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


@router.get("/daily-stats")  # 注: 定义 GET /daily-stats 接口
def get_daily_stats(limit: int = 7, session: Session = Depends(get_db_session)) -> List[Dict[str, Any]]:  # 注: 获取每日趋势数据
    """Return up to `limit` recent daily stats for charts."""

    stats = (  # 注: 查询最近 limit 天的统计数据
        session.execute(select(DailyStat).order_by(DailyStat.stat_date.desc()).limit(limit))
        .scalars()
        .all()
    )
    return [  # 注: 格式化返回列表
        {
            "date": stat.stat_date.isoformat(),  # 注: 日期
            "sync_success": stat.sync_success_count,  # 注: 同步成功数
            "sync_conflicts": stat.sync_conflict_count,  # 注: 同步冲突数
            "ai_requests": stat.ai_request_count,  # 注: AI 请求数
            "inventory_changes": stat.inventory_changes,  # 注: 库存变更数
        }
        for stat in stats
    ]


@router.get("/inventory")  # 注: 定义 GET /inventory 接口
def get_latest_inventory(limit: int = 8, session: Session = Depends(get_db_session)) -> List[Dict[str, Any]]:  # 注: 获取最新商品列表
    """Surface the latest inventory listings for dashboard cards."""

    items = (  # 注: 查询最新发布的商品及其分类
        session.execute(
            select(Item, Category)
            .join(Category, Item.category_id == Category.id)  # 注: 关联分类表
            .order_by(Item.created_at.desc())  # 注: 按创建时间倒序
            .limit(limit)
        )
        .all()
    )
    payload: List[Dict[str, Any]] = []
    for item, category in items:  # 注: 遍历结果集
        payload.append(
            {
                "id": item.id,
                "title": item.title,
                "price": float(item.price),
                "currency": "CNY",  # ✅ 硬编码默认值
                "status": item.status,
                "category": category.name if category else None,  # 注: 获取分类名称
                "created_at": item.created_at.isoformat() if isinstance(item.created_at, datetime) else None,
            }
        )
    return payload  # 注: 返回商品列表


@router.get("/sync-logs")  # 注: 定义 GET /sync-logs 接口
def get_sync_logs(limit: int = 10, session: Session = Depends(get_db_session)) -> List[Dict[str, Any]]:  # 注: 获取最近同步日志
    """Return recent sync logs for activity timeline."""

    logs = (  # 注: 查询最近的同步日志
        session.execute(select(SyncLog).order_by(SyncLog.started_at.desc()).limit(limit))
        .scalars()
        .all()
    )
    return [  # 注: 格式化日志列表
        {
            "id": log.id,
            "config_id": log.config_id,
            "status": log.status,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
        }
        for log in logs
    ]
