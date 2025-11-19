"""
购物车路由模块
处理购物车的增删改查功能
"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_current_user, get_db_session
from apps.core.models import User

router = APIRouter(prefix="/cart", tags=["购物车"])


# ==================== Pydantic Models ====================

class CartItemRequest(BaseModel):
    """添加到购物车请求"""
    item_id: int
    quantity: int = 1


class CartItemResponse(BaseModel):
    """购物车商品响应"""
    id: int
    item_id: int
    item_title: str
    item_price: float
    item_image: str
    seller_name: str
    quantity: int
    added_at: datetime
    
    class Config:
        from_attributes = True


class CartSummary(BaseModel):
    """购物车汇总"""
    items: List[CartItemResponse]
    total_items: int
    total_price: float


# ==================== API路由 ====================

@router.get("/", response_model=CartSummary)
async def get_cart(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    获取购物车内容
    """
    # TODO: 从数据库查询购物车
    
    mock_items = [
        CartItemResponse(
            id=i,
            item_id=i,
            item_title=f"购物车商品 {i}",
            item_price=999.99 + i * 100,
            item_image=f"https://picsum.photos/100/100?random={i}",
            seller_name="测试卖家",
            quantity=1,
            added_at=datetime.utcnow()
        )
        for i in range(1, 4)
    ]
    
    total_price = sum(item.item_price * item.quantity for item in mock_items)
    
    return CartSummary(
        items=mock_items,
        total_items=len(mock_items),
        total_price=total_price
    )


@router.post("/", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    payload: CartItemRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    添加商品到购物车
    """
    # TODO: 检查商品是否存在
    # TODO: 添加到购物车
    
    return CartItemResponse(
        id=1,
        item_id=payload.item_id,
        item_title="测试商品",
        item_price=999.99,
        item_image="https://picsum.photos/100/100?random=1",
        seller_name="测试卖家",
        quantity=payload.quantity,
        added_at=datetime.utcnow()
    )


@router.put("/{cart_item_id}")
async def update_cart_item(
    cart_item_id: int,
    quantity: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    更新购物车商品数量
    """
    # TODO: 更新购物车商品数量
    
    return {"message": "购物车已更新", "quantity": quantity}


@router.delete("/{cart_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(
    cart_item_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    从购物车移除商品
    """
    # TODO: 删除购物车商品
    
    return None


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    清空购物车
    """
    # TODO: 清空购物车
    
    return None
