"""
购物车路由模块
处理购物车的增删改查功能
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, delete, func
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_current_user, get_db_session
from apps.core.models import User, Item, CartItem

router = APIRouter(prefix="/cart", tags=["购物车"])


# ==================== Pydantic Models ====================

class CartItemRequest(BaseModel):
    """添加到购物车请求"""
    item_id: int = Field(..., description="商品ID")
    quantity: int = Field(default=1, ge=1, le=99, description="数量")


class CartItemUpdateRequest(BaseModel):
    """更新购物车商品请求"""
    quantity: int = Field(..., ge=1, le=99, description="数量")


class CartItemResponse(BaseModel):
    """购物车商品响应"""
    id: int
    item_id: int
    item_title: str
    item_price: float
    item_image: Optional[str] = None
    item_condition: Optional[str] = None
    seller_id: int
    seller_name: str
    quantity: int
    subtotal: float  # 小计 = 价格 * 数量
    item_status: str  # 商品状态（用于判断是否可购买）
    added_at: datetime
    
    class Config:
        from_attributes = True


class CartSummary(BaseModel):
    """购物车汇总"""
    items: List[CartItemResponse]
    total_items: int      # 商品种类数
    total_quantity: int   # 商品总数量
    total_price: float    # 总价
    available_count: int  # 可购买的商品数量
    unavailable_count: int  # 不可购买的商品数量（已下架/已售出）


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    cart_item_ids: List[int] = Field(..., description="购物车项ID列表")


# ==================== 辅助函数 ====================

def get_cart_item_response(cart_item: CartItem, item: Item, seller: User) -> CartItemResponse:
    """构建购物车商品响应对象"""
    # 获取第一张图片 - 从 medias 关系获取
    first_image = None
    if hasattr(item, 'medias') and item.medias:
        first_image = item.medias[0].url if item.medias else None
    
    return CartItemResponse(
        id=cart_item.id,
        item_id=item.id,
        item_title=item.title,
        item_price=float(item.price),
        item_image=first_image,
        item_condition=item.condition,
        seller_id=item.seller_id,
        seller_name=seller.username if seller else "未知卖家",
        quantity=cart_item.quantity,
        subtotal=float(item.price) * cart_item.quantity,
        item_status=item.status,
        added_at=cart_item.created_at or datetime.utcnow()
    )


# ==================== API路由 ====================

@router.get("", response_model=CartSummary)
async def get_cart(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    获取购物车内容
    """
    # 查询当前用户的购物车
    query = select(CartItem).where(CartItem.user_id == current_user.id)
    cart_items = session.execute(query).scalars().all()
    
    items_response = []
    total_price = 0.0
    total_quantity = 0
    available_count = 0
    unavailable_count = 0
    
    for cart_item in cart_items:
        # 获取商品信息
        item = session.get(Item, cart_item.item_id)
        if not item:
            # 商品已被删除，从购物车移除
            session.delete(cart_item)
            continue
        
        # 获取卖家信息
        seller = session.get(User, item.seller_id)
        
        # 构建响应
        item_response = get_cart_item_response(cart_item, item, seller)
        items_response.append(item_response)
        
        # 统计
        total_quantity += cart_item.quantity
        
        # 只有可购买的商品才计入总价
        if item.status == 'available':
            total_price += item_response.subtotal
            available_count += 1
        else:
            unavailable_count += 1
    
    # 提交可能的删除操作
    session.commit()
    
    return CartSummary(
        items=items_response,
        total_items=len(items_response),
        total_quantity=total_quantity,
        total_price=round(total_price, 2),
        available_count=available_count,
        unavailable_count=unavailable_count
    )


@router.get("/count")
async def get_cart_count(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    获取购物车商品数量（用于显示角标）
    """
    query = select(func.count(CartItem.id)).where(CartItem.user_id == current_user.id)
    count = session.execute(query).scalar() or 0
    
    return {"count": count}


@router.post("", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    payload: CartItemRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    添加商品到购物车
    """
    # 1. 检查商品是否存在
    item = session.get(Item, payload.item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    # 2. 检查商品状态
    if item.status != 'available':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="商品已下架或已售出，无法添加到购物车"
        )
    
    # 3. 不能购买自己的商品
    if item.seller_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能购买自己发布的商品"
        )
    
    # 4. 检查是否已在购物车中
    existing_query = select(CartItem).where(
        CartItem.user_id == current_user.id,
        CartItem.item_id == payload.item_id
    )
    existing_cart_item = session.execute(existing_query).scalar_one_or_none()
    
    if existing_cart_item:
        # 已存在则更新数量
        new_quantity = existing_cart_item.quantity + payload.quantity
        if new_quantity > 99:
            new_quantity = 99
        existing_cart_item.quantity = new_quantity
        existing_cart_item.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(existing_cart_item)
        
        seller = session.get(User, item.seller_id)
        return get_cart_item_response(existing_cart_item, item, seller)
    
    # 5. 添加新的购物车项
    cart_item = CartItem(
        user_id=current_user.id,
        item_id=payload.item_id,
        quantity=payload.quantity,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    session.add(cart_item)
    session.commit()
    session.refresh(cart_item)
    
    seller = session.get(User, item.seller_id)
    return get_cart_item_response(cart_item, item, seller)


@router.put("/{cart_item_id}", response_model=CartItemResponse)
async def update_cart_item(
    cart_item_id: int,
    payload: CartItemUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    更新购物车商品数量
    """
    # 1. 查找购物车项
    cart_item = session.get(CartItem, cart_item_id)
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="购物车项不存在"
        )
    
    # 2. 验证所有权
    if cart_item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此购物车项"
        )
    
    # 3. 检查商品是否还存在
    item = session.get(Item, cart_item.item_id)
    if not item:
        session.delete(cart_item)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品已被删除"
        )
    
    # 4. 更新数量
    cart_item.quantity = payload.quantity
    cart_item.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(cart_item)
    
    seller = session.get(User, item.seller_id)
    return get_cart_item_response(cart_item, item, seller)


@router.delete("/{cart_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(
    cart_item_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    从购物车移除商品
    """
    # 1. 查找购物车项
    cart_item = session.get(CartItem, cart_item_id)
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="购物车项不存在"
        )
    
    # 2. 验证所有权
    if cart_item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此购物车项"
        )
    
    # 3. 删除
    session.delete(cart_item)
    session.commit()
    
    return None


@router.post("/batch-delete", status_code=status.HTTP_204_NO_CONTENT)
async def batch_remove_from_cart(
    payload: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    批量删除购物车商品
    """
    if not payload.cart_item_ids:
        return None
    
    # 删除属于当前用户的指定购物车项
    stmt = delete(CartItem).where(
        CartItem.id.in_(payload.cart_item_ids),
        CartItem.user_id == current_user.id
    )
    session.execute(stmt)
    session.commit()
    
    return None


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    清空购物车
    """
    stmt = delete(CartItem).where(CartItem.user_id == current_user.id)
    session.execute(stmt)
    session.commit()
    
    return None


@router.post("/checkout-preview")
async def checkout_preview(
    cart_item_ids: List[int] = Query(None, description="要结算的购物车项ID"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    结算预览（生成订单前的确认）
    """
    # 查询购物车
    query = select(CartItem).where(CartItem.user_id == current_user.id)
    if cart_item_ids:
        query = query.where(CartItem.id.in_(cart_item_ids))
    
    cart_items = session.execute(query).scalars().all()
    
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="购物车为空或未选择商品"
        )
    
    # 构建结算预览
    checkout_items = []
    total_price = 0.0
    unavailable_items = []
    
    for cart_item in cart_items:
        item = session.get(Item, cart_item.item_id)
        if not item:
            continue
        
        seller = session.get(User, item.seller_id)
        
        if item.status != 'available':
            unavailable_items.append({
                "item_id": item.id,
                "title": item.title,
                "reason": "已下架" if item.status == 'inactive' else "已售出"
            })
            continue
        
        subtotal = float(item.price) * cart_item.quantity
        total_price += subtotal
        
        checkout_items.append({
            "cart_item_id": cart_item.id,
            "item_id": item.id,
            "title": item.title,
            "price": float(item.price),
            "quantity": cart_item.quantity,
            "subtotal": subtotal,
            "seller_id": item.seller_id,
            "seller_name": seller.username if seller else "未知卖家"
        })
    
    if not checkout_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有可结算的商品"
        )
    
    return {
        "items": checkout_items,
        "total_price": round(total_price, 2),
        "total_items": len(checkout_items),
        "unavailable_items": unavailable_items
    }
