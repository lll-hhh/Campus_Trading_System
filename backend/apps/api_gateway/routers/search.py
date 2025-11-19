"""
搜索功能路由 - 高级搜索、自动补全、搜索建议
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_current_user, get_db_session


router = APIRouter()


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
    # TODO: 实现基于Elasticsearch或数据库的自动补全
    # 当前返回模拟数据
    
    suggestions = []
    
    # 模拟关键词建议
    keywords = [
        "iPhone 15", "MacBook Pro", "iPad", "AirPods",
        "小米手机", "华为手机", "耳机", "充电器"
    ]
    for kw in keywords:
        if query.lower() in kw.lower():
            suggestions.append(SearchSuggestion(
                text=kw,
                type="keyword",
                count=100 + len(kw) * 10
            ))
    
    # 模拟分类建议
    categories = ["数码产品", "图书教材", "生活用品", "服装配饰"]
    for cat in categories:
        if query in cat:
            suggestions.append(SearchSuggestion(
                text=cat,
                type="category",
                count=50
            ))
    
    # 限制返回数量
    suggestions = suggestions[:limit]
    
    return SearchAutoCompleteResponse(
        suggestions=suggestions,
        total=len(suggestions)
    )


@router.get("/search", response_model=SearchResultResponse)
async def advanced_search(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类筛选"),
    min_price: Optional[float] = Query(None, ge=0, description="最低价格"),
    max_price: Optional[float] = Query(None, ge=0, description="最高价格"),
    status: Optional[str] = Query(None, description="商品状态：在售/已售出"),
    sort_by: str = Query("relevance", description="排序方式：relevance/price_asc/price_desc/time_desc/popular"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db_session),
    current_user: Optional[dict] = Depends(get_current_user)
) -> SearchResultResponse:
    """
    高级搜索
    
    支持：
    - 关键词搜索（标题、描述）
    - 多条件筛选（分类、价格区间、状态）
    - 多种排序方式
    - 结果高亮
    """
    # TODO: 实现真实的搜索逻辑
    # 当前返回模拟数据
    
    # 保存搜索历史
    if current_user:
        # TODO: 保存到search_history表
        pass
    
    # 模拟搜索结果
    mock_items = [
        {
            "id": 1,
            "title": f"iPhone 15 Pro Max 256GB 深空黑 - {q}",
            "price": 8999.00,
            "image": "https://via.placeholder.com/200",
            "category": "数码产品",
            "seller_name": "张三",
            "seller_avatar": "https://via.placeholder.com/50",
            "view_count": 1234,
            "favorite_count": 56,
            "status": "在售",
            "created_at": datetime.utcnow(),
            "highlight": f"全新未拆封，支持官方验机。搜索词：<em>{q}</em>"
        },
        {
            "id": 2,
            "title": f"MacBook Air M2 13寸 - {q}",
            "price": 7499.00,
            "image": "https://via.placeholder.com/200",
            "category": "数码产品",
            "seller_name": "李四",
            "seller_avatar": None,
            "view_count": 890,
            "favorite_count": 34,
            "status": "在售",
            "created_at": datetime.utcnow(),
            "highlight": f"9成新，仅用3个月。关键词：<em>{q}</em>"
        },
        {
            "id": 3,
            "title": f"AirPods Pro 2代 - {q}",
            "price": 1599.00,
            "image": "https://via.placeholder.com/200",
            "category": "数码产品",
            "seller_name": "王五",
            "seller_avatar": "https://via.placeholder.com/50",
            "view_count": 567,
            "favorite_count": 23,
            "status": "在售",
            "created_at": datetime.utcnow(),
            "highlight": f"原装正品，配件齐全。包含：<em>{q}</em>"
        }
    ]
    
    # 应用筛选条件
    filtered_items = mock_items.copy()
    
    if category:
        filtered_items = [item for item in filtered_items if item["category"] == category]
    
    if min_price is not None:
        filtered_items = [item for item in filtered_items if item["price"] >= min_price]
    
    if max_price is not None:
        filtered_items = [item for item in filtered_items if item["price"] <= max_price]
    
    if status:
        filtered_items = [item for item in filtered_items if item["status"] == status]
    
    # 应用排序
    if sort_by == "price_asc":
        filtered_items.sort(key=lambda x: x["price"])
    elif sort_by == "price_desc":
        filtered_items.sort(key=lambda x: x["price"], reverse=True)
    elif sort_by == "time_desc":
        filtered_items.sort(key=lambda x: x["created_at"], reverse=True)
    elif sort_by == "popular":
        filtered_items.sort(key=lambda x: x["view_count"], reverse=True)
    
    # 分页
    total = len(filtered_items)
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered_items[start:end]
    
    # 相关搜索建议
    suggestions = [
        f"{q} 二手",
        f"{q} 全新",
        f"{q} 配件",
        f"便宜的{q}"
    ]
    
    return SearchResultResponse(
        items=[SearchResultItem(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        query=q,
        suggestions=suggestions
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
    # TODO: 从数据库统计真实的热门搜索
    # 当前返回模拟数据
    
    popular_keywords = [
        PopularSearch(keyword="iPhone 15", count=1234, trend="up"),
        PopularSearch(keyword="MacBook", count=890, trend="stable"),
        PopularSearch(keyword="AirPods", count=756, trend="up"),
        PopularSearch(keyword="iPad", count=654, trend="down"),
        PopularSearch(keyword="小米手机", count=543, trend="up"),
        PopularSearch(keyword="华为手机", count=432, trend="stable"),
        PopularSearch(keyword="机械键盘", count=321, trend="up"),
        PopularSearch(keyword="显示器", count=287, trend="stable"),
        PopularSearch(keyword="耳机", count=234, trend="down"),
        PopularSearch(keyword="充电宝", count=198, trend="stable"),
    ]
    
    return PopularSearchResponse(
        keywords=popular_keywords[:limit],
        updated_at=datetime.utcnow()
    )


@router.get("/history", response_model=SearchHistoryResponse)
async def get_search_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> SearchHistoryResponse:
    """
    获取用户搜索历史
    
    需要登录
    """
    # TODO: 从数据库读取真实的搜索历史
    # 当前返回模拟数据
    
    user_id = current_user["id"]
    
    mock_history = [
        SearchHistoryItem(
            id=1,
            keyword="iPhone 15",
            searched_at=datetime.utcnow(),
            result_count=45
        ),
        SearchHistoryItem(
            id=2,
            keyword="MacBook Pro",
            searched_at=datetime.utcnow(),
            result_count=23
        ),
        SearchHistoryItem(
            id=3,
            keyword="AirPods",
            searched_at=datetime.utcnow(),
            result_count=67
        )
    ]
    
    # 分页
    total = len(mock_history)
    start = (page - 1) * page_size
    end = start + page_size
    history = mock_history[start:end]
    
    return SearchHistoryResponse(
        history=history,
        total=total
    )


@router.delete("/history/{history_id}")
async def delete_search_history(
    history_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> dict:
    """
    删除单条搜索历史
    """
    # TODO: 实现真实的删除逻辑
    
    return {
        "success": True,
        "message": "搜索历史已删除"
    }


@router.delete("/history")
async def clear_search_history(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> dict:
    """
    清空搜索历史
    """
    # TODO: 实现真实的清空逻辑
    user_id = current_user["id"]
    
    return {
        "success": True,
        "message": "搜索历史已清空"
    }


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1),
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
    # TODO: 实现智能建议算法
    
    suggestions = {
        "related_searches": [
            f"{query} 二手",
            f"{query} 全新",
            f"便宜的{query}"
        ],
        "hot_keywords": [
            "iPhone 15",
            "MacBook",
            "AirPods"
        ],
        "categories": [
            "数码产品",
            "图书教材"
        ]
    }
    
    return suggestions
