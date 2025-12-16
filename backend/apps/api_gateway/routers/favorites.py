from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc
from pydantic import BaseModel

from apps.api_gateway.dependencies import get_current_user, get_db_session
from apps.core.models.inventory import Favorite, Item

router = APIRouter(prefix="/favorites", tags=["favorites"])


class FavoriteItemDto(BaseModel):
    item_id: int
    title: str
    price: float
    currency: str = "CNY"
    status: str
    condition: str = "good"
    cover_image: Optional[str] = None
    favorited_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[FavoriteItemDto])
async def get_my_favorites(
    current_user=Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """获取当前用户的收藏列表"""
    user_id = current_user.id

    # ✅ 修复：只选择数据库中存在的列
    stmt = (
        select(
            Favorite.created_at.label("favorited_at"),
            Item.id.label("item_id"),
            Item.title,
            Item.price,
            Item.status,
            Item.condition_type,  # ✅ 使用正确的字段名
        )
        .join(Item, Favorite.item_id == Item.id)
        .where(Favorite.user_id == user_id)
        .order_by(desc(Favorite.created_at))
        .offset(skip)
        .limit(limit)
    )

    results = db.execute(stmt).all()

    # 条件映射
    condition_map = {
        "全新": "new",
        "99新": "like_new", 
        "95新": "very_good",
        "9成新": "good",
        "二手": "used",
    }

    # 构建响应
    items = []
    seen_ids = set()
    for row in results:
        if row.item_id not in seen_ids:
            seen_ids.add(row.item_id)
            items.append(FavoriteItemDto(
                item_id=row.item_id,
                title=row.title,
                price=float(row.price),
                currency="CNY",
                status=row.status or "available",
                condition=condition_map.get(row.condition_type, "used"),
                cover_image=None,  # 可以单独查询
                favorited_at=row.favorited_at
            ))

    return items


@router.post("/{item_id}", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    item_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """添加收藏"""
    # 检查商品是否存在
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 检查是否已收藏
    existing = db.execute(
        select(Favorite).where(
            and_(Favorite.user_id == current_user.id, Favorite.item_id == item_id)
        )
    ).scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="已经收藏过了")
    
    # 添加收藏
    favorite = Favorite(user_id=current_user.id, item_id=item_id)
    db.add(favorite)
    db.commit()
    
    return {"message": "收藏成功"}


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    item_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """取消收藏"""
    favorite = db.execute(
        select(Favorite).where(
            and_(Favorite.user_id == current_user.id, Favorite.item_id == item_id)
        )
    ).scalar_one_or_none()
    
    if not favorite:
        raise HTTPException(status_code=404, detail="未收藏该商品")
    
    db.delete(favorite)
    db.commit()


@router.get("/{item_id}/check", response_model=bool)
async def check_is_favorited(
    item_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """检查是否已收藏"""
    favorite = db.execute(
        select(Favorite).where(
            and_(Favorite.user_id == current_user.id, Favorite.item_id == item_id)
        )
    ).scalar_one_or_none()
    
    return favorite is not None