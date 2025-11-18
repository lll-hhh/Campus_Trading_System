"""Trade service router definitions with 4-database sync and transaction management."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from apps.core.database import db_manager
from apps.services.db_operations import db_operation_service

router = APIRouter(prefix="/trade", tags=["trade"])


class OfferPayload(BaseModel):
    """Offer creation payload."""

    item_id: int
    buyer_id: int
    price: float


class TransactionPayload(BaseModel):
    """Transaction creation payload."""
    
    buyer_id: int
    seller_id: int
    item_id: int
    amount: float


@router.get("/offers")
def list_offers() -> list[dict[str, str]]:
    """Return mock offers."""

    return [{"status": "open", "item_id": 1}]


@router.post("/offers")
def create_offer(payload: OfferPayload) -> dict[str, str | float]:
    """Create an offer placeholder."""

    return {"status": "created", "price": payload.price}


@router.post("/transactions", status_code=201)
def create_transaction(payload: TransactionPayload) -> dict[str, any]:
    """
    Create a transaction with automatic sync to all 4 databases.
    
    Uses ACID transaction to:
    1. Create transaction record
    2. Update item status to 'sold'
    3. Sync to all databases (MySQL/MariaDB/PostgreSQL/SQLite)
    
    Features:
    - Deadlock detection and automatic retry
    - REPEATABLE READ isolation level (MySQL)
    - Pessimistic locking (FOR UPDATE)
    """
    with db_manager.session_scope("mysql") as session:
        # 1. 创建交易记录(四库同步)
        transaction_data = {
            'buyer_id': payload.buyer_id,
            'seller_id': payload.seller_id,
            'item_id': payload.item_id,
            'amount': payload.amount,
            'status': 'pending',
        }
        
        transaction_id = db_operation_service.insert_with_sync(
            session=session,
            table='transactions',
            data=transaction_data,
            sync_to_all=True,
        )
        
        # 2. 更新商品状态为已售(四库同步)
        update_result = db_operation_service.update_with_sync(
            session=session,
            table='items',
            record_id=payload.item_id,
            data={'status': 'sold'},
            sync_to_all=True,
        )
        
        if update_result == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Item {payload.item_id} not found"
            )
        
        return {
            "transaction_id": transaction_id,
            "item_id": payload.item_id,
            "buyer_id": payload.buyer_id,
            "seller_id": payload.seller_id,
            "amount": payload.amount,
            "status": "pending",
            "item_status": "sold",
            "synced_to": ["mysql", "mariadb", "postgres", "sqlite"],
            "message": "Transaction created and item marked as sold across all databases",
        }


@router.put("/transactions/{transaction_id}/status", status_code=200)
def update_transaction_status(
    transaction_id: int,
    status: str,
) -> dict[str, any]:
    """
    Update transaction status with automatic sync to all 4 databases.
    
    Valid statuses: pending, completed, cancelled
    """
    valid_statuses = ['pending', 'completed', 'cancelled']
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    with db_manager.session_scope("mysql") as session:
        rowcount = db_operation_service.update_with_sync(
            session=session,
            table='transactions',
            record_id=transaction_id,
            data={'status': status},
            sync_to_all=True,
        )
        
        if rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Transaction {transaction_id} not found"
            )
        
        return {
            "transaction_id": transaction_id,
            "status": status,
            "synced_to": ["mysql", "mariadb", "postgres", "sqlite"],
            "message": f"Transaction status updated to '{status}' across all databases",
        }
