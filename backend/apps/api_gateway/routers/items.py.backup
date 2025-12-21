"""
商品管理路由模块
处理商品的增删改查、搜索、分类等功能
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, desc, or_, and_
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_current_user, get_db_session
from apps.core.models import User

router = APIRouter(prefix="/items", tags=["商品管理"])


# ==================== Pydantic Models ====================

class ItemCreateRequest(BaseModel):
    """创建商品请求"""
    title: str = Field(..., min_length=5, max_length=100, description="商品标题")
    category: str = Field(..., description="商品分类")
    condition: str = Field(..., description="商品成色")
    price: float = Field(..., gt=0, description="商品价格")
    original_price: Optional[float] = Field(None, description="原价")
    description: str = Field(..., min_length=10, description="商品描述")
    location: str = Field(..., description="交易地点")
    contact_method: str = Field(default="chat", description="联系方式")
    phone: Optional[str] = Field(None, description="手机号")
    wechat: Optional[str] = Field(None, description="微信号")
    allow_bargain: bool = Field(default=True, description="是否支持议价")
    accept_return: bool = Field(default=False, description="是否支持退换")
    images: List[str] = Field(default=[], description="商品图片URL列表")


class ItemUpdateRequest(BaseModel):
    """更新商品请求"""
    title: Optional[str] = Field(None, min_length=5, max_length=100)
    category: Optional[str] = None
    condition: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    original_price: Optional[float] = None
    description: Optional[str] = Field(None, min_length=10)
    location: Optional[str] = None
    contact_method: Optional[str] = None
    phone: Optional[str] = None
    wechat: Optional[str] = None
    allow_bargain: Optional[bool] = None
    accept_return: Optional[bool] = None
    images: Optional[List[str]] = None
    status: Optional[str] = None


class ItemResponse(BaseModel):
    """商品响应"""
    id: int
    title: str
    category: str
    condition: str
    price: float
    original_price: Optional[float] = None
    description: str
    location: str
    status: str
    views: int
    likes: int
    seller_id: int
    seller_name: str
    images: List[str]
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ItemListResponse(BaseModel):
    """商品列表响应"""
    items: List[ItemResponse]
    total: int
    page: int
    page_size: int


# ==================== API路由 ====================

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: ItemCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    发布新商品
    
    需要登录，商品默认为草稿状态
    """
    from apps.core.models import Item, Category, ItemMedia
    from sqlalchemy import select
    
    # 查找或创建分类
    category = session.execute(
        select(Category).where(Category.name == (payload.category or "其他"))
    ).scalar_one_or_none()
    
    if not category:
        category = Category(
            name=payload.category or "其他",
            description=f"{payload.category or '其他'}分类"
        )
        session.add(category)
        session.flush()
    
    # 创建商品
    new_item = Item(
        seller_id=current_user.id,
        category_id=category.id,
        title=payload.title,
        description=payload.description,
        price=payload.price,
        currency="CNY",
        status="available" if payload.status == "published" else "draft",
        condition=payload.condition or "good",
        view_count=0
    )
    session.add(new_item)
    session.flush()
    
    # 添加图片
    if payload.images:
        for img_url in payload.images:
            media = ItemMedia(
                item_id=new_item.id,
                media_type="image",
                url=img_url
            )
            session.add(media)
    
    session.commit()
    session.refresh(new_item)
    
    return ItemResponse(
        id=new_item.id,
        title=new_item.title,
        description=new_item.description,
        price=float(new_item.price),
        category=category.name,
        images=[m.url for m in new_item.medias],
        status=new_item.status,
        seller_id=new_item.seller_id,
        seller_name=current_user.username,
        view_count=new_item.view_count,
        favorite_count=0,
        created_at=new_item.created_at,
        updated_at=new_item.updated_at
    )


@router.get("/", response_model=ItemListResponse)
async def get_items(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    min_price: Optional[float] = Query(None, ge=0, description="最低价格"),
    max_price: Optional[float] = Query(None, ge=0, description="最高价格"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    session: Session = Depends(get_db_session)
):
    """
    获取商品列表
    
    支持分页、筛选、搜索、排序
    """
    # TODO: 从数据库查询商品列表
    # 这里返回模拟数据
    
    mock_items = [
        ItemResponse(
            id=i,
            title=f"商品 {i}",
            category="数码产品",
            condition="全新",
            price=999.99 + i * 100,
            original_price=1999.99 + i * 100,
            description="这是一个测试商品",
            location="北京大学",
            status="在售",
            views=100 + i * 10,
            likes=10 + i,
            seller_id=1,
            seller_name="测试用户",
            images=["https://picsum.photos/200/200?random=" + str(i)],
            created_at=datetime.utcnow()
        )
        for i in range(1, min(page_size + 1, 11))
    ]
    
    return ItemListResponse(
        items=mock_items,
        total=100,
        page=page,
        page_size=page_size
    )


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    session: Session = Depends(get_db_session)
):
    """
    获取商品详情
    """
    # TODO: 从数据库查询商品详情
    # 这里返回模拟数据
    
    return ItemResponse(
        id=item_id,
        title="全新iPad Pro 2024款 11英寸",
        category="数码产品",
        condition="全新",
        price=4999,
        original_price=6999,
        description="全新未拆封的iPad Pro 2024款",
        location="北京大学 学生公寓1号楼",
        status="在售",
        views=1258,
        likes=89,
        seller_id=1,
        seller_name="张同学",
        images=[
            "https://picsum.photos/800/600?random=1",
            "https://picsum.photos/800/600?random=2"
        ],
        created_at=datetime.utcnow()
    )


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    payload: ItemUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    更新商品信息
    
    只有商品发布者可以更新
    """
    # TODO: 查询商品并验证所有权
    # TODO: 更新商品信息
    
    return ItemResponse(
        id=item_id,
        title=payload.title or "商品标题",
        category=payload.category or "数码产品",
        condition=payload.condition or "全新",
        price=payload.price or 999,
        description=payload.description or "商品描述",
        location=payload.location or "北京大学",
        status=payload.status or "在售",
        views=100,
        likes=10,
        seller_id=current_user.id,
        seller_name=current_user.username,
        images=payload.images or [],
        created_at=datetime.utcnow()
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    删除商品
    
    只有商品发布者可以删除
    """
    # TODO: 查询商品并验证所有权
    # TODO: 删除商品
    
    return None


@router.post("/{item_id}/favorite")
async def toggle_favorite(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    收藏/取消收藏商品
    """
    # TODO: 切换收藏状态
    
    return {"message": "收藏成功", "is_favorited": True}


@router.post("/{item_id}/view")
async def increment_view(
    item_id: int,
    session: Session = Depends(get_db_session)
):
    """
    增加商品浏览次数
    """
    # TODO: 增加浏览计数
    
    return {"message": "浏览次数已更新"}


@router.get("/{item_id}/similar", response_model=List[ItemResponse])
async def get_similar_items(
    item_id: int,
    limit: int = Query(4, ge=1, le=20, description="返回数量"),
    session: Session = Depends(get_db_session)
):
    """
    获取相似商品推荐
    """
    # TODO: 基于分类、价格等推荐相似商品
    
    mock_items = [
        ItemResponse(
            id=i,
            title=f"相似商品 {i}",
            category="数码产品",
            condition="全新",
            price=999.99 + i * 100,
            description="相似商品描述",
            location="北京大学",
            status="在售",
            views=100,
            likes=10,
            seller_id=1,
            seller_name="测试用户",
            images=["https://picsum.photos/200/200?random=" + str(i + 100)],
            created_at=datetime.utcnow()
        )
        for i in range(1, limit + 1)
    ]
    
    return mock_items


@router.get("/categories/list")
async def get_categories():
    """
    获取所有商品分类
    """
    return {
        "categories": [
            {"label": "📱 数码产品", "value": "digital", "count": 125},
            {"label": "📚 教材书籍", "value": "books", "count": 89},
            {"label": "👕 服装鞋帽", "value": "clothing", "count": 67},
            {"label": "🏀 运动器材", "value": "sports", "count": 45},
            {"label": "🎮 娱乐休闲", "value": "entertainment", "count": 56},
            {"label": "🛏️ 生活用品", "value": "daily", "count": 78},
            {"label": "🎨 文具办公", "value": "stationery", "count": 34},
            {"label": "🎸 乐器设备", "value": "music", "count": 23},
            {"label": "🚲 自行车", "value": "bicycle", "count": 12},
            {"label": "📦 其他", "value": "other", "count": 91}
        ]
    }


@router.get("/my-items", response_model=ItemListResponse)
async def get_my_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="商品状态筛选"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    获取当前用户发布的商品
    """
    # TODO: 查询用户的商品
    
    mock_items = [
        ItemResponse(
            id=i,
            title=f"我的商品 {i}",
            category="数码产品",
            condition="全新",
            price=999.99,
            description="我发布的商品",
            location="北京大学",
            status="在售" if i % 2 == 0 else "已售出",
            views=100 + i * 10,
            likes=10 + i,
            seller_id=current_user.id,
            seller_name=current_user.username,
            images=["https://picsum.photos/200/200?random=" + str(i)],
            created_at=datetime.utcnow()
        )
        for i in range(1, min(page_size + 1, 6))
    ]
    
    return ItemListResponse(
        items=mock_items,
        total=20,
        page=page,
        page_size=page_size
    )
