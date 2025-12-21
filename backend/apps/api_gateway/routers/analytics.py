"""高级分析和复杂SQL查询路由"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import text

from apps.core.database import db_manager

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ============================================
# 响应模型
# ============================================

class TopSellerResponse(BaseModel):
    """顶级卖家数据"""
    user_id: int
    username: str
    total_sales: int
    total_revenue: float
    avg_price: float
    rating: float


class PriceTrendResponse(BaseModel):
    """价格趋势数据"""
    category_name: str
    avg_price: float
    min_price: float
    max_price: float
    item_count: int
    price_change_pct: float


class UserBehaviorResponse(BaseModel):
    """用户行为分析"""
    hour: int
    active_users: int
    transactions: int
    avg_transaction_amount: float


class CategoryAnalysisResponse(BaseModel):
    """分类分析数据"""
    category_id: int
    category_name: str
    item_count: int
    sold_count: int
    sell_through_rate: float
    avg_price: float
    total_revenue: float


class ComplexSearchResponse(BaseModel):
    """复杂搜索结果"""
    item_id: int
    title: str
    price: float
    seller_name: str
    category_name: str
    view_count: int
    transaction_count: int
    avg_rating: float
    days_listed: int


# ============================================
# 1. 多表连接查询 - 销售排行榜
# ============================================

@router.get("/top-sellers", response_model=List[TopSellerResponse])
def get_top_sellers(
    limit: int = Query(10, ge=1, le=100),
    days: int = Query(30, ge=1, le=365)
) -> List[TopSellerResponse]:
    """
    查询顶级卖家排行榜
    
    使用技术:
    - 多表JOIN (users + transactions + items)
    - 聚合函数 (COUNT, SUM, AVG)
    - 分组查询 (GROUP BY)
    - 子查询 (计算平均评分)
    - 时间范围过滤
    """
    with db_manager.session_scope("mysql") as session:
        # 计算截止日期
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 复杂SQL: 多表连接 + 聚合 + 子查询
        # 使用 transactions 表中的 seller_rating 字段作为评分
        query = text("""
            SELECT 
                u.id as user_id,
                u.username,
                COUNT(DISTINCT t.id) as total_sales,
                COALESCE(SUM(t.final_amount), 0) as total_revenue,
                COALESCE(AVG(i.price), 0) as avg_price,
                COALESCE(
                    (SELECT AVG(t2.seller_rating) 
                     FROM transactions t2 
                     WHERE t2.seller_id = u.id 
                       AND t2.seller_rating IS NOT NULL), 
                    0
                ) as rating
            FROM users u
            LEFT JOIN transactions t ON u.id = t.seller_id 
                AND t.status = 'completed' 
                AND t.created_at >= :cutoff_date
            LEFT JOIN items i ON t.item_id = i.id
            GROUP BY u.id, u.username
            HAVING total_sales > 0
            ORDER BY total_revenue DESC, total_sales DESC
            LIMIT :limit
        """)
        
        result = session.execute(
            query,
            {"cutoff_date": cutoff_date, "limit": limit}
        ).fetchall()
        
        return [
            TopSellerResponse(
                user_id=row.user_id,
                username=row.username,
                total_sales=row.total_sales,
                total_revenue=float(row.total_revenue),
                avg_price=float(row.avg_price),
                rating=float(row.rating)
            )
            for row in result
        ]


# ============================================
# 2. 嵌套子查询 - 价格趋势分析
# ============================================

@router.get("/price-trends", response_model=List[PriceTrendResponse])
def get_price_trends() -> List[PriceTrendResponse]:
    """
    分析各分类价格趋势
    
    使用技术:
    - 嵌套子查询 (当前价格 vs 历史价格)
    - 窗口函数模拟 (价格变化百分比)
    - CASE WHEN条件聚合
    - LEFT JOIN + COALESCE
    """
    with db_manager.session_scope("mysql") as session:
        query = text("""
            SELECT 
                c.id as category_id,
                c.name as category_name,
                COALESCE(AVG(i.price), 0) as avg_price,
                COALESCE(MIN(i.price), 0) as min_price,
                COALESCE(MAX(i.price), 0) as max_price,
                COUNT(i.id) as item_count,
                COALESCE(
                    (
                        (AVG(i.price) - 
                         (SELECT AVG(i2.price) 
                          FROM items i2 
                          WHERE i2.category_id = c.id 
                            AND i2.created_at < DATE_SUB(NOW(), INTERVAL 30 DAY)
                         )
                        ) / 
                        NULLIF((SELECT AVG(i2.price) 
                                FROM items i2 
                                WHERE i2.category_id = c.id 
                                  AND i2.created_at < DATE_SUB(NOW(), INTERVAL 30 DAY)
                               ), 0) * 100
                    ), 0
                ) as price_change_pct
            FROM categories c
            LEFT JOIN items i ON c.id = i.category_id 
                AND i.status != 'deleted'
            GROUP BY c.id, c.name
            HAVING item_count > 0
            ORDER BY avg_price DESC
        """)
        
        result = session.execute(query).fetchall()
        
        return [
            PriceTrendResponse(
                category_name=row.category_name,
                avg_price=float(row.avg_price),
                min_price=float(row.min_price),
                max_price=float(row.max_price),
                item_count=row.item_count,
                price_change_pct=float(row.price_change_pct)
            )
            for row in result
        ]


# ============================================
# 3. 时间序列分析 - 用户行为模式
# ============================================

@router.get("/user-behavior", response_model=List[UserBehaviorResponse])
def get_user_behavior_pattern() -> List[UserBehaviorResponse]:
    """
    分析用户行为模式 (按小时统计)
    
    使用技术:
    - 时间函数 (HOUR, DATE)
    - 聚合分组 (GROUP BY小时)
    - DISTINCT去重
    - 条件过滤 (最近7天)
    """
    with db_manager.session_scope("mysql") as session:
        query = text("""
            SELECT 
                HOUR(t.created_at) as hour,
                COUNT(DISTINCT t.buyer_id) as active_users,
                COUNT(t.id) as transactions,
                COALESCE(AVG(t.final_amount), 0) as avg_transaction_amount
            FROM transactions t
            WHERE t.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                AND t.status != 'cancelled'
            GROUP BY hour
            ORDER BY hour
        """)
        
        result = session.execute(query).fetchall()
        
        return [
            UserBehaviorResponse(
                hour=row.hour,
                active_users=row.active_users,
                transactions=row.transactions,
                avg_transaction_amount=float(row.avg_transaction_amount)
            )
            for row in result
        ]


# ============================================
# 4. 复杂聚合 - 分类销售分析
# ============================================

@router.get("/category-analysis", response_model=List[CategoryAnalysisResponse])
def get_category_analysis() -> List[CategoryAnalysisResponse]:
    """
    分类销售分析
    
    使用技术:
    - CASE WHEN条件聚合
    - 计算字段 (售罄率)
    - 多条件JOIN
    - 子查询计算收入
    """
    with db_manager.session_scope("mysql") as session:
        query = text("""
            SELECT 
                c.id as category_id,
                c.name as category_name,
                COUNT(i.id) as item_count,
                SUM(CASE WHEN i.status = 'sold' THEN 1 ELSE 0 END) as sold_count,
                (SUM(CASE WHEN i.status = 'sold' THEN 1 ELSE 0 END) * 100.0 / 
                 NULLIF(COUNT(i.id), 0)) as sell_through_rate,
                COALESCE(AVG(i.price), 0) as avg_price,
                COALESCE(
                    (SELECT SUM(t.final_amount) 
                     FROM transactions t 
                     JOIN items i2 ON t.item_id = i2.id 
                     WHERE i2.category_id = c.id 
                       AND t.status = 'completed'
                    ), 0
                ) as total_revenue
            FROM categories c
            LEFT JOIN items i ON c.id = i.category_id 
                AND i.status != 'deleted'
            GROUP BY c.id, c.name
            ORDER BY total_revenue DESC
        """)
        
        result = session.execute(query).fetchall()
        
        return [
            CategoryAnalysisResponse(
                category_id=row.category_id,
                category_name=row.category_name,
                item_count=row.item_count,
                sold_count=row.sold_count,
                sell_through_rate=float(row.sell_through_rate or 0),
                avg_price=float(row.avg_price),
                total_revenue=float(row.total_revenue)
            )
            for row in result
        ]


# ============================================
# 5. 超复杂搜索 - 多维度商品筛选
# ============================================

@router.get("/complex-search", response_model=List[ComplexSearchResponse])
def complex_item_search(
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    category_id: Optional[int] = None,
    min_rating: Optional[float] = None,
    min_transactions: Optional[int] = None,
    sort_by: str = Query("popularity", regex="^(popularity|price|rating|recent)$"),
    limit: int = Query(20, ge=1, le=100)
) -> List[ComplexSearchResponse]:
    """
    超复杂多条件商品搜索
    
    使用技术:
    - 4表JOIN (items + users + categories + transactions)
    - 动态WHERE条件
    - 聚合函数 + HAVING
    - 多字段排序
    - DATEDIFF日期计算
    """
    with db_manager.session_scope("mysql") as session:
        # 构建动态WHERE条件
        conditions = ["i.status = 'available'"]
        params = {"limit": limit}
        
        if min_price is not None:
            conditions.append("i.price >= :min_price")
            params["min_price"] = min_price
            
        if max_price is not None:
            conditions.append("i.price <= :max_price")
            params["max_price"] = max_price
            
        if category_id is not None:
            conditions.append("i.category_id = :category_id")
            params["category_id"] = category_id
        
        where_clause = " AND ".join(conditions)
        
        # 排序逻辑
        order_by_map = {
            "popularity": "view_count DESC, transaction_count DESC",
            "price": "i.price ASC",
            "rating": "avg_rating DESC",
            "recent": "i.created_at DESC"
        }
        order_clause = order_by_map.get(sort_by, "view_count DESC")
        
        # 使用 transactions 表中的 seller_rating 作为评分来源
        query = text(f"""
            SELECT 
                i.id as item_id,
                i.title,
                i.price,
                u.username as seller_name,
                c.name as category_name,
                i.view_count,
                COUNT(DISTINCT t.id) as transaction_count,
                COALESCE(AVG(t.seller_rating), 0) as avg_rating,
                DATEDIFF(NOW(), i.created_at) as days_listed
            FROM items i
            JOIN users u ON i.seller_id = u.id
            LEFT JOIN categories c ON i.category_id = c.id
            LEFT JOIN transactions t ON i.id = t.item_id 
                AND t.status != 'cancelled'
            WHERE {where_clause}
            GROUP BY i.id, i.title, i.price, u.username, c.name, 
                     i.view_count, i.created_at
            {"HAVING avg_rating >= :min_rating" if min_rating else ""}
            {"AND transaction_count >= :min_transactions" if min_transactions else ""}
            ORDER BY {order_clause}
            LIMIT :limit
        """)
        
        if min_rating is not None:
            params["min_rating"] = min_rating
        if min_transactions is not None:
            params["min_transactions"] = min_transactions
        
        result = session.execute(query, params).fetchall()
        
        return [
            ComplexSearchResponse(
                item_id=row.item_id,
                title=row.title,
                price=float(row.price),
                seller_name=row.seller_name,
                category_name=row.category_name or "未分类",
                view_count=row.view_count,
                transaction_count=row.transaction_count,
                avg_rating=float(row.avg_rating),
                days_listed=row.days_listed
            )
            for row in result
        ]


# ============================================
# 6. 相关性推荐 - 协同过滤查询
# ============================================

@router.get("/recommendations/{user_id}")
def get_recommendations(user_id: int, limit: int = 10) -> Dict:
    """
    基于协同过滤的商品推荐
    
    使用技术:
    - 自连接 (找相似用户)
    - NOT IN子查询 (排除已购买)
    - 多层嵌套查询
    - 权重计算
    """
    with db_manager.session_scope("mysql") as session:
        query = text("""
            SELECT 
                i.id,
                i.title,
                i.price,
                COUNT(DISTINCT t2.buyer_id) as similar_user_count,
                (COUNT(DISTINCT t2.buyer_id) * AVG(i.view_count)) as score
            FROM items i
            JOIN transactions t2 ON i.id = t2.item_id
            WHERE t2.buyer_id IN (
                -- 找到购买过相似商品的用户
                SELECT DISTINCT t1.buyer_id
                FROM transactions t1
                WHERE t1.item_id IN (
                    -- 当前用户购买过的商品所在分类
                    SELECT i2.category_id
                    FROM transactions t0
                    JOIN items i2 ON t0.item_id = i2.id
                    WHERE t0.buyer_id = :user_id
                )
                AND t1.buyer_id != :user_id
            )
            AND i.id NOT IN (
                -- 排除用户已购买的商品
                SELECT item_id FROM transactions WHERE buyer_id = :user_id
            )
            AND i.status = 'available'
            GROUP BY i.id, i.title, i.price, i.view_count
            ORDER BY score DESC
            LIMIT :limit
        """)
        
        result = session.execute(
            query,
            {"user_id": user_id, "limit": limit}
        ).fetchall()
        
        return {
            "user_id": user_id,
            "recommendations": [
                {
                    "item_id": row.id,
                    "title": row.title,
                    "price": float(row.price),
                    "relevance_score": float(row.score),
                    "similar_users": row.similar_user_count
                }
                for row in result
            ]
        }
