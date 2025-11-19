"""
收藏路由模块
处理商品收藏、收藏列表管理等功能
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_current_user, get_db_session
from apps.core.models import User

router = APIRouter(prefix="/favorites", tags=["收藏管理"])


# ==================== Pydantic Models ====================

class FavoriteItemResponse(BaseModel):
    """收藏商品响应"""
    id: int
    item_id: int
    item_title: str
    item_price: float
    item_image: str
    item_status: str
    seller_name: str
    favorited_at: datetime
    
    class Config:
        from_attributes = True


class FavoriteListResponse(BaseModel):
    """收藏列表响应"""
    favorites: List[FavoriteItemResponse]
    total: int
    page: int
    page_size: int


# ==================== API路由 ====================

@router.post("/{item_id}", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    收藏商品
    
    如果已经收藏则返回已收藏信息
    """
    # TODO: 检查商品是否存在
    # TODO: 检查是否已收藏
    # TODO: 创建收藏记录
    
    return {
        "message": "收藏成功",
        "item_id": item_id,
        "favorited_at": datetime.utcnow()
    }


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    取消收藏
    """
    # TODO: 删除收藏记录
    
    return None


@router.get("/", response_model=FavoriteListResponse)
async def get_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="商品状态筛选"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    获取收藏列表
    
    支持按商品状态筛选（在售、已售出等）
    """
    # TODO: 查询用户收藏列表
    
    mock_favorites = [
        FavoriteItemResponse(
            id=i,
            item_id=i,
            item_title=f"收藏的商品 {i}",
            item_price=999.99 + i * 100,
            item_image=f"https://picsum.photos/200/200?random={i}",
            item_status="在售" if i % 2 == 0 else "已售出",
            seller_name=f"卖家{i}",
            favorited_at=datetime.utcnow()
        )
        for i in range(1, min(page_size + 1, 11))
    ]
    
    return FavoriteListResponse(
        favorites=mock_favorites,
        total=50,
        page=page,
        page_size=page_size
    )


@router.get("/check/{item_id}")
async def check_favorite(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    检查商品是否已收藏
    """
    # TODO: 查询收藏记录
    
    # 模拟：奇数ID已收藏
    is_favorited = item_id % 2 == 1
    
    return {
        "item_id": item_id,
        "is_favorited": is_favorited
    }


@router.get("/statistics")
async def get_favorite_statistics(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    获取收藏统计信息
    """
    # TODO: 统计收藏数据
    
    return {
        "total_favorites": 50,
        "available_items": 35,
        "sold_items": 15,
        "categories": {
            "数码产品": 20,
            "教材书籍": 15,
            "服装鞋帽": 10,
            "其他": 5
        }
    }
