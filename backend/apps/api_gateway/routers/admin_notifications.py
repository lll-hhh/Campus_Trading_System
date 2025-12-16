"""Admin notification management endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select, update
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_current_admin_user, get_db_session
from apps.core.models import Notification, User

router = APIRouter(prefix="/admin/notifications", tags=["admin-notifications"])


@router.get("/list")
def list_notifications(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_admin_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_read: bool | None = None,
    type_filter: str | None = None,
) -> dict[str, Any]:
    """
    获取通知列表（管理员可查看所有通知或特定用户通知）
    """
    query = select(Notification)
    
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
    if type_filter:
        query = query.where(Notification.type == type_filter)
    
    # 计数
    count_stmt = select(Notification.id).select_from(Notification)
    if is_read is not None:
        count_stmt = count_stmt.where(Notification.is_read == is_read)
    if type_filter:
        count_stmt = count_stmt.where(Notification.type == type_filter)
    total = len(db.execute(count_stmt).fetchall())
    
    # 分页
    query = query.order_by(desc(Notification.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    notifications = db.execute(query).scalars().all()
    
    return {
        "items": [
            {
                "id": n.id,
                "user_id": n.user_id,
                "type": n.type,
                "title": n.title,
                "content": n.content,
                "related_id": n.related_id,
                "related_type": n.related_type,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/{notification_id}/mark-read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """标记通知为已读"""
    stmt = (
        update(Notification)
        .where(Notification.id == notification_id)
        .values(is_read=True, updated_at=datetime.utcnow())
    )
    result = db.execute(stmt)
    db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    return {"message": "已标记为已读"}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_admin_user),
) -> dict[str, Any]:
    """删除通知"""
    notification = db.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    db.delete(notification)
    db.commit()
    
    return {"message": "通知已删除"}
