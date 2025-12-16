"""
搜索功能路由 - 高级搜索、自动补全、搜索建议
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import (
    get_current_user,
    get_current_user_optional,
    get_db_session,
)
from apps.core.models.users import User
from apps.services.business_logic import SearchService


router = APIRouter(prefix="/search", tags=["搜索功能"])


# ==================== Pydantic Models ====================

class SearchSuggestion(BaseModel):
    """搜索建议项"""
    text: str
    type: str  # keyword, category, item
    count: Optional[int] = None


class SearchAutoCompleteResponse(BaseModel):
    """自动补全响应"""
    suggestions: List[SearchSuggestion]
    total: int


class SearchResultItem(BaseModel):
    """搜索结果项"""
    id: int
    title: str
    price: float
    image: str
    category: str
    seller_name: str
    seller_avatar: Optional[str] = None
    view_count: int
    favorite_count: int
    status: str
    created_at: datetime
    highlight: Optional[str] = None  # 高亮的摘要


class SearchResultResponse(BaseModel):
    """搜索结果响应"""
    items: List[SearchResultItem]
    total: int
    page: int
    page_size: int
    query: str
    suggestions: List[str] = []  # 相关搜索建议


class PopularSearch(BaseModel):
    """热门搜索"""
    keyword: str
    count: int
    trend: str  # up, down, stable


class PopularSearchResponse(BaseModel):
    """热门搜索响应"""
    keywords: List[PopularSearch]
    updated_at: datetime


class SearchHistoryItem(BaseModel):
    """搜索历史项"""
    id: int
    keyword: str
    searched_at: datetime
    result_count: int


class SearchHistoryResponse(BaseModel):
    """搜索历史响应"""
    history: List[SearchHistoryItem]
    total: int


# ==================== API Endpoints ====================

@router.get("/autocomplete", response_model=SearchAutoCompleteResponse)
async def search_autocomplete(
    query: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db_session)
) -> SearchAutoCompleteResponse:
    """
    搜索自动补全
    
    返回匹配的关键词、分类、商品标题建议
    """
    try:
        result = SearchService.get_autocomplete(db, query, limit)
        return SearchAutoCompleteResponse(
            suggestions=[SearchSuggestion(**s) for s in result["suggestions"]],
            total=result["total"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"自动补全失败: {str(e)}"
        )


@router.get("/search", response_model=SearchResultResponse)
async def advanced_search(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类筛选"),
    min_price: Optional[float] = Query(None, ge=0, description="最低价格"),
    max_price: Optional[float] = Query(None, ge=0, description="最高价格"),
    item_status: Optional[str] = Query("available", description="商品状态"),
    sort_by: str = Query("relevance", description="排序方式：relevance/price_asc/price_desc/time_desc/popular"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db_session),
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> SearchResultResponse:
    """
    高级搜索
    
    支持：
    - 关键词搜索（标题、描述）
    - 多条件筛选（分类、价格区间、状态）
    - 多种排序方式
    - 结果高亮
    """
    try:
        user_id = None
        if current_user:
            user_id = getattr(current_user, "id", None)
        result = SearchService.search_items(
            session=db,
            keyword=q,
            category=category,
            min_price=min_price,
            max_price=max_price,
            status=item_status or "available",
            sort_by=sort_by,
            page=page,
            page_size=page_size,
            user_id=user_id
        )
        db.commit()  # 提交搜索历史和热门统计
        
        return SearchResultResponse(
            items=[SearchResultItem(**item) for item in result["items"]],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            query=result["query"],
            suggestions=result["suggestions"]
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )


@router.get("/popular", response_model=PopularSearchResponse)
async def get_popular_searches(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db_session)
) -> PopularSearchResponse:
    """
    获取热门搜索关键词
    
    基于搜索频率统计，展示实时热搜榜
    """
    try:
        result = SearchService.get_popular_searches(db, limit)
        return PopularSearchResponse(
            keywords=[PopularSearch(**kw) for kw in result["keywords"]],
            updated_at=result["updated_at"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取热门搜索失败: {str(e)}"
        )


@router.get("/history", response_model=SearchHistoryResponse)
async def get_search_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> SearchHistoryResponse:
    """
    获取用户搜索历史
    
    需要登录
    """
    try:
        user_id = getattr(current_user, "id")
        result = SearchService.get_search_history(db, user_id, page, page_size)
        return SearchHistoryResponse(
            history=[SearchHistoryItem(**h) for h in result["history"]],
            total=result["total"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取搜索历史失败: {str(e)}"
        )


@router.delete("/history/{history_id}")
async def delete_search_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> dict:
    """
    删除单条搜索历史
    """
    try:
        user_id = getattr(current_user, "id")
        result = SearchService.delete_search_history(db, user_id, history_id)
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )


@router.delete("/history")
async def clear_search_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> dict:
    """
    清空搜索历史
    """
    try:
        user_id = getattr(current_user, "id")
        result = SearchService.clear_search_history(db, user_id)
        db.commit()
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清空失败: {str(e)}"
        )


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db_session)
) -> dict:
    """
    智能搜索建议
    
    基于：
    - 用户历史搜索
    - 热门搜索
    - 相关商品标题
    - 分类匹配
    """
    try:
        user_id = getattr(current_user, "id", None) if current_user else None
        return SearchService.get_search_suggestions(db, query, user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取建议失败: {str(e)}"
        )
