"""
实现完整的商品路由 - 使用业务逻辑服务
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_current_user, get_db_session
from apps.core.models import User
from apps.services.business_logic import ItemService, FavoriteService

router = APIRouter(prefix="/items", tags=["商品管理"])


# ==================== Pydantic Models ====================

class ItemCreateRequest(BaseModel):
    """创建商品请求"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    category: str = Field(default="其他")
    images: List[str] = Field(default_factory=list)
    status: str = Field(default="draft")
    condition: str = Field(default="good")


class ItemUpdateRequest(BaseModel):
    """更新商品请求"""
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = None
    condition: Optional[str] = None


class ItemResponse(BaseModel):
    """商品响应"""
    id: int
    title: str
    description: str
    price: float
    category: str
    images: List[str]
    status: str
    condition: str = "good"
    seller_id: int
    seller_name: str
    view_count: int
    favorite_count: int
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
    """发布新商品"""
    from apps.core.models import Category, ItemMedia
    
    item = ItemService.create_item(
        session=session,
        seller_id=current_user.id,
        title=payload.title,
        description=payload.description,
        price=payload.price,
        category_name=payload.category,
        images=payload.images,
        status=payload.status,
        condition=payload.condition
    )
    
    # 构建响应
    category = session.get(Category, item.category_id)
    medias = session.execute(
        select(ItemMedia).where(ItemMedia.item_id == item.id)
    ).scalars().all()
    
    return ItemResponse(
        id=item.id,
        title=item.title,
        description=item.description,
        price=float(item.price),
        category=category.name if category else "其他",
        images=[m.url for m in medias],
        status=item.status,
        condition=item.condition,
        seller_id=item.seller_id,
        seller_name=current_user.username,
        view_count=item.view_count,
        favorite_count=0,
        created_at=item.created_at,
        updated_at=item.updated_at
    )


@router.get("/", response_model=ItemListResponse)
async def get_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    status: str = "available",
    session: Session = Depends(get_db_session)
):
    """获取商品列表"""
    from apps.core.models import Category, ItemMedia
    from sqlalchemy import select
    
    items, total = ItemService.get_items(
        session=session,
        page=page,
        page_size=page_size,
        category=category,
        min_price=min_price,
        max_price=max_price,
        keyword=keyword,
        status=status
    )
    
    # 转换为响应格式
    items_data = []
    for item in items:
        cat = session.get(Category, item.category_id)
        seller = session.get(User, item.seller_id)
        medias = session.execute(
            select(ItemMedia).where(ItemMedia.item_id == item.id)
        ).scalars().all()
        
        items_data.append(ItemResponse(
            id=item.id,
            title=item.title,
            description=item.description,
            price=float(item.price),
            category=cat.name if cat else "其他",
            images=[m.url for m in medias],
            status=item.status,
            condition=item.condition,
            seller_id=item.seller_id,
            seller_name=seller.username if seller else "未知",
            view_count=item.view_count,
            favorite_count=0,
            created_at=item.created_at,
            updated_at=item.updated_at
        ))
    
    return ItemListResponse(
        items=items_data,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    session: Session = Depends(get_db_session)
):
    """获取商品详情"""
    from apps.core.models import Category, ItemMedia
    from sqlalchemy import select
    
    item = ItemService.get_item_detail(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    cat = session.get(Category, item.category_id)
    seller = session.get(User, item.seller_id)
    medias = session.execute(
        select(ItemMedia).where(ItemMedia.item_id == item.id)
    ).scalars().all()
    
    return ItemResponse(
        id=item.id,
        title=item.title,
        description=item.description,
        price=float(item.price),
        category=cat.name if cat else "其他",
        images=[m.url for m in medias],
        status=item.status,
        condition=item.condition,
        seller_id=item.seller_id,
        seller_name=seller.username if seller else "未知",
        view_count=item.view_count,
        favorite_count=0,
        created_at=item.created_at,
        updated_at=item.updated_at
    )


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    payload: ItemUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """更新商品信息"""
    from apps.core.models import Category, ItemMedia
    from sqlalchemy import select
    
    update_data = payload.dict(exclude_unset=True)
    item = ItemService.update_item(session, item_id, current_user.id, **update_data)
    
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在或无权限")
    
    cat = session.get(Category, item.category_id)
    medias = session.execute(
        select(ItemMedia).where(ItemMedia.item_id == item.id)
    ).scalars().all()
    
    return ItemResponse(
        id=item.id,
        title=item.title,
        description=item.description,
        price=float(item.price),
        category=cat.name if cat else "其他",
        images=[m.url for m in medias],
        status=item.status,
        condition=item.condition,
        seller_id=item.seller_id,
        seller_name=current_user.username,
        view_count=item.view_count,
        favorite_count=0,
        created_at=item.created_at,
        updated_at=item.updated_at
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """删除商品"""
    success = ItemService.delete_item(session, item_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="商品不存在或无权限")
    return None


@router.post("/{item_id}/favorite")
async def toggle_favorite(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """切换收藏状态"""
    result = FavoriteService.toggle_favorite(session, current_user.id, item_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@router.get("/my/favorites", response_model=ItemListResponse)
async def get_my_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """获取我的收藏"""
    from apps.core.models import Category, ItemMedia
    from sqlalchemy import select
    
    items, total = FavoriteService.get_user_favorites(
        session, current_user.id, page, page_size
    )
    
    items_data = []
    for item in items:
        cat = session.get(Category, item.category_id)
        seller = session.get(User, item.seller_id)
        medias = session.execute(
            select(ItemMedia).where(ItemMedia.item_id == item.id)
        ).scalars().all()
        
        items_data.append(ItemResponse(
            id=item.id,
            title=item.title,
            description=item.description,
            price=float(item.price),
            category=cat.name if cat else "其他",
            images=[m.url for m in medias],
            status=item.status,
            condition=item.condition,
            seller_id=item.seller_id,
            seller_name=seller.username if seller else "未知",
            view_count=item.view_count,
            favorite_count=0,
            created_at=item.created_at,
            updated_at=item.updated_at
        ))
    
    return ItemListResponse(
        items=items_data,
        total=total,
        page=page,
        page_size=page_size
    )
