"""
订单/交易路由模块
处理订单的创建、查询、状态更新等功能
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_current_user, get_db_session
from apps.core.models import User

router = APIRouter(prefix="/orders", tags=["订单管理"])


# ==================== Pydantic Models ====================

class OrderCreateRequest(BaseModel):
    """创建订单请求"""
    item_id: int
    quantity: int = 1
    delivery_address: Optional[str] = None
    note: Optional[str] = None


class OrderItemResponse(BaseModel):
    """订单商品信息"""
    item_id: int
    item_title: str
    item_price: float
    item_image: str
    quantity: int


class OrderResponse(BaseModel):
    """订单响应"""
    id: int
    order_no: str
    buyer_id: int
    buyer_name: str
    seller_id: int
    seller_name: str
    items: List[OrderItemResponse]
    total_amount: float
    status: str  # pending, paid, shipped, completed, cancelled, refunded
    payment_method: Optional[str] = None
    delivery_address: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
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
    status: str = Field(..., description="订单状态")
    note: Optional[str] = Field(None, description="备注信息")


# ==================== API路由 ====================

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    创建订单
    
    从购物车或商品详情页直接购买时创建订单
    """
    # TODO: 验证商品是否存在且可购买
    # TODO: 创建订单记录
    # TODO: 更新商品库存
    
    order_no = f"ORD{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{current_user.id}"
    
    return OrderResponse(
        id=1,
        order_no=order_no,
        buyer_id=current_user.id,
        buyer_name=current_user.username,
        seller_id=100,
        seller_name="测试卖家",
        items=[
            OrderItemResponse(
                item_id=payload.item_id,
                item_title="测试商品",
                item_price=999.99,
                item_image="https://picsum.photos/100/100?random=1",
                quantity=payload.quantity
            )
        ],
        total_amount=999.99 * payload.quantity,
        status="pending",
        delivery_address=payload.delivery_address,
        note=payload.note,
        created_at=datetime.utcnow()
    )


@router.get("/", response_model=OrderListResponse)
async def get_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="订单状态筛选"),
    role: str = Query("buyer", description="buyer或seller"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    获取订单列表
    
    role='buyer': 我的购买订单
    role='seller': 我的销售订单
    """
    # TODO: 根据role查询买家或卖家订单
    
    mock_orders = [
        OrderResponse(
            id=i,
            order_no=f"ORD202411190001{i}",
            buyer_id=current_user.id if role == "buyer" else 200,
            buyer_name=current_user.username if role == "buyer" else "买家用户",
            seller_id=200 if role == "buyer" else current_user.id,
            seller_name="卖家用户" if role == "buyer" else current_user.username,
            items=[
                OrderItemResponse(
                    item_id=i,
                    item_title=f"订单商品 {i}",
                    item_price=999.99,
                    item_image=f"https://picsum.photos/100/100?random={i}",
                    quantity=1
                )
            ],
            total_amount=999.99,
            status=["pending", "paid", "shipped", "completed"][i % 4],
            created_at=datetime.utcnow()
        )
        for i in range(1, min(page_size + 1, 6))
    ]
    
    return OrderListResponse(
        orders=mock_orders,
        total=20,
        page=page,
        page_size=page_size
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    获取订单详情
    
    只能查看自己的订单（买家或卖家）
    """
    # TODO: 查询订单并验证权限
    
    return OrderResponse(
        id=order_id,
        order_no=f"ORD20241119000{order_id}",
        buyer_id=current_user.id,
        buyer_name=current_user.username,
        seller_id=100,
        seller_name="测试卖家",
        items=[
            OrderItemResponse(
                item_id=1,
                item_title="iPad Pro 2024款",
                item_price=4999.00,
                item_image="https://picsum.photos/100/100?random=1",
                quantity=1
            )
        ],
        total_amount=4999.00,
        status="paid",
        payment_method="alipay",
        delivery_address="北京大学 学生公寓1号楼",
        note="请在工作日配送",
        created_at=datetime.utcnow()
    )


@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    payload: OrderStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    更新订单状态
    
    买家: 可以取消订单、确认收货
    卖家: 可以确认发货、拒绝订单
    """
    # TODO: 验证订单权限
    # TODO: 验证状态转换是否合法
    # TODO: 更新订单状态
    
    return OrderResponse(
        id=order_id,
        order_no=f"ORD20241119000{order_id}",
        buyer_id=current_user.id,
        buyer_name=current_user.username,
        seller_id=100,
        seller_name="测试卖家",
        items=[
            OrderItemResponse(
                item_id=1,
                item_title="测试商品",
                item_price=999.99,
                item_image="https://picsum.photos/100/100?random=1",
                quantity=1
            )
        ],
        total_amount=999.99,
        status=payload.status,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@router.post("/{order_id}/pay")
async def pay_order(
    order_id: int,
    payment_method: str = Query(..., description="支付方式: alipay/wechat/balance"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    支付订单
    
    集成支付接口（支付宝、微信、余额支付）
    """
    # TODO: 验证订单状态
    # TODO: 调用支付接口
    # TODO: 更新订单状态
    
    return {
        "message": "支付成功",
        "order_id": order_id,
        "payment_method": payment_method,
        "amount": 999.99
    }


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    reason: Optional[str] = Query(None, description="取消原因"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    取消订单
    
    只能取消未支付或已支付但未发货的订单
    """
    # TODO: 验证订单状态
    # TODO: 处理退款（如果已支付）
    # TODO: 恢复库存
    
    return {
        "message": "订单已取消",
        "order_id": order_id,
        "reason": reason
    }


@router.post("/{order_id}/refund")
async def refund_order(
    order_id: int,
    reason: str = Query(..., description="退款原因"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    申请退款
    
    买家可以对已支付的订单申请退款
    """
    # TODO: 创建退款申请
    # TODO: 通知卖家
    
    return {
        "message": "退款申请已提交",
        "order_id": order_id,
        "reason": reason
    }


@router.get("/statistics/summary")
async def get_order_statistics(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    获取订单统计信息
    
    买家: 购买统计
    卖家: 销售统计
    """
    # TODO: 统计订单数据
    
    return {
        "total_orders": 25,
        "pending_orders": 3,
        "completed_orders": 20,
        "cancelled_orders": 2,
        "total_amount": 24999.50,
        "this_month_amount": 5999.00
    }
