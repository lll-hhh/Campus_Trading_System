"""Inventory service router definitions with 4-database sync."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from apps.core.database import db_manager
from apps.core.models import Category, Item
from apps.services.db_operations import db_operation_service

router = APIRouter(prefix="/inventory", tags=["inventory"])


class ItemPayload(BaseModel):
    """Payload describing item creation or update."""

    seller_id: int = Field(..., gt=0)
    title: str
    category_id: int
    price: float
    description: str | None = None
    currency: str = "CNY"


@router.get("/items")
def list_items(limit: int = 20) -> list[dict[str, str | float | int | None]]:
    """Return latest listings from the primary database."""

    with db_manager.session_scope("mysql") as session:
        items = (
            session.execute(
                select(Item).order_by(Item.created_at.desc()).limit(limit)
            )
            .scalars()
            .all()
        )

    return [
        {
            "id": item.id,
            "title": item.title,
            "price": float(item.price),
            "currency": item.currency,
            "status": item.status,
            "category_id": item.category_id,
        }
        for item in items
    ]


@router.post("/items", status_code=201)
def create_item(payload: ItemPayload) -> dict[str, str | int | float]:
    """
    Create a new item listing with automatic sync to all 4 databases.
    
    Uses transaction management with deadlock retry.
    Syncs to: MySQL, MariaDB, PostgreSQL, SQLite
    """
    # 先验证分类存在(从主库查询)
    with db_manager.session_scope("mysql") as session:
        category = session.get(Category, payload.category_id)
        if category is None:
            raise HTTPException(status_code=400, detail="Category not found")
    
    # 使用统一服务插入并同步到所有数据库
    with db_manager.session_scope("mysql") as session:
        item_data = {
            'seller_id': payload.seller_id,
            'category_id': payload.category_id,
            'title': payload.title,
            'description': payload.description or "",
            'price': payload.price,
            'currency': payload.currency,
            'status': 'draft',
        }
        
        # 自动同步到四个数据库
        item_id = db_operation_service.insert_with_sync(
            session=session,
            table='items',
            data=item_data,
            sync_to_all=True,
        )
        
        return {
            "id": item_id,
            "title": payload.title,
            "status": "draft",
            "price": float(payload.price),
            "synced_to": ["mysql", "mariadb", "postgres", "sqlite"],
        }


@router.put("/items/{item_id}", status_code=200)
def update_item(item_id: int, payload: ItemPayload) -> dict[str, str | int]:
    """
    Update an item with automatic sync to all 4 databases.
    
    Uses optimistic locking and transaction management.
    """
    with db_manager.session_scope("mysql") as session:
        update_data = {
            'title': payload.title,
            'description': payload.description or "",
            'price': payload.price,
            'currency': payload.currency,
        }
        
        # 自动同步到四个数据库
        rowcount = db_operation_service.update_with_sync(
            session=session,
            table='items',
            record_id=item_id,
            data=update_data,
            sync_to_all=True,
        )
        
        if rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        
        return {
            "id": item_id,
            "message": "Item updated successfully",
            "synced_to": ["mysql", "mariadb", "postgres", "sqlite"],
        }


@router.delete("/items/{item_id}", status_code=200)
def delete_item(item_id: int) -> dict[str, str | int]:
    """
    Delete an item with automatic sync to all 4 databases.
    
    Uses transaction management with deadlock retry.
    """
    with db_manager.session_scope("mysql") as session:
        # 自动同步到四个数据库
        rowcount = db_operation_service.delete_with_sync(
            session=session,
            table='items',
            record_id=item_id,
            sync_to_all=True,
        )
        
        if rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        
        return {
            "id": item_id,
            "message": "Item deleted successfully",
            "synced_to": ["mysql", "mariadb", "postgres", "sqlite"],
        }


@router.get("/items/{item_id}/sync-status")
def check_item_sync_status(item_id: int) -> dict[str, any]:
    """
    Verify that an item is consistent across all 4 databases.
    
    Returns sync status and any inconsistencies.
    """
    result = db_operation_service.verify_sync_consistency(
        table='items',
        record_id=item_id,
    )
    
    return {
        "item_id": item_id,
        "consistent": result['consistent'],
        "databases_checked": result['databases_checked'],
        "records": result['records'],
    }


@router.get("/sync-status")
def get_sync_status() -> dict[str, any]:
    """
    Get overall synchronization status for all databases.
    
    Returns connection status and isolation levels.
    """
    return db_operation_service.get_sync_status()
