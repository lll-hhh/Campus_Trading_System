"""
完整的订单/交易路由实现
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_current_user, get_db_session
from apps.core.models import User, Item
from apps.services.business_logic import TransactionService

router = APIRouter(prefix="/orders", tags=["订单管理"])


# ==================== Pydantic Models ====================

class OrderCreateRequest(BaseModel):
    """创建订单请求"""
    item_id: int = Field(..., description="商品ID")
    buyer_contact: Optional[str] = Field(None, max_length=200, description="买家联系方式")


class OrderItemInfo(BaseModel):
    """订单商品信息"""
    item_id: int
    item_title: str
    item_price: float


class OrderResponse(BaseModel):
    """订单响应"""
    id: int
    buyer_id: int
    buyer_name: str
    seller_id: int
    seller_name: str
    item_info: OrderItemInfo
    total_amount: float
    status: str
    buyer_contact: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """订单列表响应"""
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int


class OrderStatusUpdateRequest(BaseModel):
    """订单状态更新请求"""
    status: str = Field(..., description="新状态")


# ==================== API路由 ====================

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """创建订单"""
    transaction = TransactionService.create_transaction(
        session=session,
        buyer_id=current_user.id,
        item_id=payload.item_id,
        buyer_contact=payload.buyer_contact
    )
    
    if not transaction:
        raise HTTPException(status_code=400, detail="商品不可用或已下架")
    
    # 获取商品和卖家信息
    item = session.get(Item, transaction.item_id)
    seller = session.get(User, transaction.seller_id)
    
    return OrderResponse(
        id=transaction.id,
        buyer_id=transaction.buyer_id,
        buyer_name=current_user.username,
        seller_id=transaction.seller_id,
        seller_name=seller.username if seller else "未知",
        item_info=OrderItemInfo(
            item_id=item.id,
            item_title=item.title,
            item_price=float(transaction.item_price)
        ),
        total_amount=float(transaction.final_amount),
        status=transaction.status,
        buyer_contact=transaction.buyer_contact,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at
    )


@router.get("", response_model=OrderListResponse)
async def get_orders(
    role: str = Query("buyer", description="buyer或seller"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """获取订单列表"""
    transactions, total = TransactionService.get_user_transactions(
        session, current_user.id, role, page, page_size
    )
    
    # 转换为响应格式
    orders_data = []
    for trans in transactions:
        item = session.get(Item, trans.item_id)
        buyer = session.get(User, trans.buyer_id)
        seller = session.get(User, trans.seller_id)
        
        orders_data.append(OrderResponse(
            id=trans.id,
            buyer_id=trans.buyer_id,
            buyer_name=buyer.username if buyer else "未知",
            seller_id=trans.seller_id,
            seller_name=seller.username if seller else "未知",
            item_info=OrderItemInfo(
                item_id=item.id if item else 0,
                item_title=item.title if item else "商品已删除",
                item_price=float(trans.item_price)
            ),
            total_amount=float(trans.final_amount),
            status=trans.status,
            buyer_contact=trans.buyer_contact,
            created_at=trans.created_at,
            updated_at=trans.updated_at
        ))
    
    return OrderListResponse(
        orders=orders_data,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """获取订单详情"""
    from apps.core.models import Transaction
    
    transaction = session.get(Transaction, order_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    # 验证权限
    if transaction.buyer_id != current_user.id and transaction.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限查看此订单")
    
    item = session.get(Item, transaction.item_id)
    buyer = session.get(User, transaction.buyer_id)
    seller = session.get(User, transaction.seller_id)
    
    return OrderResponse(
        id=transaction.id,
        buyer_id=transaction.buyer_id,
        buyer_name=buyer.username if buyer else "未知",
        seller_id=transaction.seller_id,
        seller_name=seller.username if seller else "未知",
        item_info=OrderItemInfo(
            item_id=item.id if item else 0,
            item_title=item.title if item else "商品已删除",
            item_price=float(transaction.item_price)
        ),
        total_amount=float(transaction.final_amount),
        status=transaction.status,
        buyer_contact=transaction.buyer_contact,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at
    )


@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    payload: OrderStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """更新订单状态"""
    
    transaction = TransactionService.update_transaction_status(
        session, order_id, current_user.id, payload.status
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="订单不存在或无权限")
    
    item = session.get(Item, transaction.item_id)
    buyer = session.get(User, transaction.buyer_id)
    seller = session.get(User, transaction.seller_id)
    
    return OrderResponse(
        id=transaction.id,
        buyer_id=transaction.buyer_id,
        buyer_name=buyer.username if buyer else "未知",
        seller_id=transaction.seller_id,
        seller_name=seller.username if seller else "未知",
        item_info=OrderItemInfo(
            item_id=item.id if item else 0,
            item_title=item.title if item else "商品已删除",
            item_price=float(transaction.item_price)
        ),
        total_amount=float(transaction.final_amount),
        status=transaction.status,
        buyer_contact=transaction.buyer_contact,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at
    )


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """取消订单"""
    return await update_order_status(
        order_id,
        OrderStatusUpdateRequest(status="cancelled"),
        current_user,
        session
    )


@router.post("/{order_id}/complete", response_model=OrderResponse)
async def complete_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """完成订单"""
    return await update_order_status(
        order_id,
        OrderStatusUpdateRequest(status="completed"),
        current_user,
        session
    )
