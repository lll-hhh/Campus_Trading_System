"""
管理员高级查询API
支持多表JOIN查询、复杂SQL构建
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_db_session, require_roles
from apps.core.models import User

router = APIRouter(prefix="/admin/query", tags=["admin-query"])


class JoinConfig(BaseModel):
    """JOIN配置"""
    table: str = Field(..., description="关联表名")
    type: str = Field("LEFT", description="JOIN类型: INNER, LEFT, RIGHT")
    on: str = Field(..., description="关联条件，如: items.seller_id = users.id")
    alias: Optional[str] = Field(None, description="表别名")


class ColumnConfig(BaseModel):
    """列配置"""
    name: str = Field(..., description="列名或表达式，如 COUNT(*), users.username")
    alias: Optional[str] = Field(None, description="别名")
    table: Optional[str] = Field(None, description="所属表（用于前缀）")


class QueryRequest(BaseModel):
    """复杂查询请求"""
    base_table: str = Field(..., description="主表名")
    columns: List[ColumnConfig] = Field(..., description="查询列")
    joins: Optional[List[JoinConfig]] = Field(None, description="关联配置")
    where: Optional[str] = Field(None, description="WHERE条件")
    group_by: Optional[str] = Field(None, description="GROUP BY子句")
    having: Optional[str] = Field(None, description="HAVING子句")
    order_by: Optional[str] = Field(None, description="排序")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)


class QueryTemplate(BaseModel):
    """查询模板"""
    name: str
    description: str
    request: QueryRequest


# 安全的表名白名单
ALLOWED_TABLES = {
    'users', 'user_profiles', 'items', 'categories', 'transactions',
    'comments', 'messages', 'conversations', 'notifications',
    'conflict_records', 'sync_logs', 'audit_logs', 'cart_items',
    'search_history', 'search_trending', 'user_activities',
    'roles', 'permissions', 'role_permissions', 'system_settings'
}


def validate_table_name(table: str) -> bool:
    """验证表名是否在白名单中"""
    return table.lower() in ALLOWED_TABLES


def sanitize_sql_identifier(identifier: str) -> str:
    """清理SQL标识符，防止注入"""
    # 移除危险字符
    dangerous_chars = [';', '--', '/*', '*/', 'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE']
    identifier_upper = identifier.upper()
    for char in dangerous_chars:
        if char in identifier_upper:
            raise HTTPException(status_code=400, detail=f"不允许的SQL操作: {char}")
    return identifier


@router.post("/execute")
async def execute_query(
    request: QueryRequest,
    session: Session = Depends(get_db_session),
    _: User = Depends(require_roles("admin"))
) -> Dict[str, Any]:
    """
    执行复杂SQL查询
    
    示例请求：
    ```json
    {
        "base_table": "items",
        "columns": [
            {"name": "id", "table": "items"},
            {"name": "title", "table": "items"},
            {"name": "username", "table": "users", "alias": "seller_name"},
            {"name": "name", "table": "categories", "alias": "category_name"}
        ],
        "joins": [
            {"table": "users", "on": "items.seller_id = users.id"},
            {"table": "categories", "on": "items.category_id = categories.id"}
        ],
        "where": "items.status = 'available'",
        "order_by": "items.created_at DESC"
    }
    ```
    """
    
    try:
        # 验证主表
        if not validate_table_name(request.base_table):
            raise HTTPException(status_code=400, detail=f"不允许访问的表: {request.base_table}")
        
        # 验证JOIN表
        if request.joins:
            for join in request.joins:
                if not validate_table_name(join.table):
                    raise HTTPException(status_code=400, detail=f"不允许访问的表: {join.table}")
                # 清理关联条件
                sanitize_sql_identifier(join.on)
        
        # 清理WHERE条件
        if request.where:
            sanitize_sql_identifier(request.where)
        
        # 构建SELECT子句
        select_parts = []
        for col in request.columns:
            # 构建列表达式
            if col.table:
                col_expr = f"{col.table}.{col.name}"
            else:
                col_expr = col.name
            
            # 添加别名
            if col.alias:
                col_expr += f" AS {col.alias}"
            
            select_parts.append(col_expr)
        
        select_clause = ", ".join(select_parts) if select_parts else "*"
        
        # 构建JOIN子句
        join_clause = ""
        if request.joins:
            for join in request.joins:
                alias = f" {join.alias}" if join.alias else ""
                join_clause += f"\n{join.type} JOIN {join.table}{alias} ON {join.on}"
        
        # 构建WHERE子句
        where_clause = ""
        if request.where:
            where_clause = f"\nWHERE {request.where}"
        
        # 构建GROUP BY子句
        group_by_clause = ""
        if request.group_by:
            sanitize_sql_identifier(request.group_by)
            group_by_clause = f"\nGROUP BY {request.group_by}"
        
        # 构建HAVING子句
        having_clause = ""
        if request.having:
            sanitize_sql_identifier(request.having)
            having_clause = f"\nHAVING {request.having}"
        
        # 构建ORDER BY子句
        order_clause = ""
        if request.order_by:
            sanitize_sql_identifier(request.order_by)
            order_clause = f"\nORDER BY {request.order_by}"
        
        # 分页
        offset = (request.page - 1) * request.page_size
        limit_clause = f"\nLIMIT {request.page_size} OFFSET {offset}"
        
        # 完整SQL
        sql = f"""
            SELECT {select_clause}
            FROM {request.base_table}
            {join_clause}
            {where_clause}
            {group_by_clause}
            {having_clause}
            {order_clause}
            {limit_clause}
        """.strip()
        
        # 执行查询
        result = session.execute(text(sql))
        rows = result.fetchall()
        
        # 转换为字典列表
        data = []
        column_names = result.keys()
        for row in rows:
            row_dict = {}
            for i, col_name in enumerate(column_names):
                value = row[i]
                # 处理特殊类型
                if hasattr(value, 'isoformat'):  # datetime
                    value = value.isoformat()
                row_dict[col_name] = value
            data.append(row_dict)
        
        # 获取总数（不带LIMIT）
        count_sql = f"""
            SELECT COUNT(*)
            FROM {request.base_table}
            {join_clause}
            {where_clause}
            {group_by_clause}
            {having_clause}
        """.strip()
        
        total_result = session.execute(text(count_sql))
        total = total_result.scalar()
        
        return {
            "data": data,
            "total": total or 0,
            "page": request.page,
            "page_size": request.page_size,
            "sql": sql  # 返回生成的SQL（方便调试）
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"查询执行失败: {str(e)}"
        )


@router.get("/templates")
async def get_query_templates(
    _: User = Depends(require_roles("admin"))
) -> Dict[str, List[QueryTemplate]]:
    """获取预定义查询模板"""
    templates = [
        QueryTemplate(
            name="商品详情（含卖家和分类）",
            description="查询商品信息，包括卖家名称和分类名称",
            request=QueryRequest(
                base_table="items",
                columns=[
                    ColumnConfig(name="id", table="items"),
                    ColumnConfig(name="title", table="items"),
                    ColumnConfig(name="price", table="items"),
                    ColumnConfig(name="status", table="items"),
                    ColumnConfig(name="username", table="users", alias="seller_name"),
                    ColumnConfig(name="email", table="users", alias="seller_email"),
                    ColumnConfig(name="credit_score", table="users", alias="seller_credit"),
                    ColumnConfig(name="name", table="categories", alias="category_name"),
                    ColumnConfig(name="created_at", table="items")
                ],
                joins=[
                    JoinConfig(table="users", on="items.seller_id = users.id"),
                    JoinConfig(table="categories", type="LEFT", on="items.category_id = categories.id")
                ],
                order_by="items.created_at DESC",
                page=1,
                page_size=20
            )
        ),
        QueryTemplate(
            name="用户交易统计",
            description="统计每个用户的交易次数和总金额",
            request=QueryRequest(
                base_table="users",
                columns=[
                    ColumnConfig(name="id", table="users"),
                    ColumnConfig(name="username", table="users"),
                    ColumnConfig(name="email", table="users"),
                    ColumnConfig(name="COUNT(transactions.id)", alias="transaction_count"),
                    ColumnConfig(name="COALESCE(SUM(transactions.final_amount), 0)", alias="total_amount"),
                    ColumnConfig(name="COALESCE(AVG(transactions.final_amount), 0)", alias="avg_amount")
                ],
                joins=[
                    JoinConfig(
                        table="transactions",
                        type="LEFT",
                        on="users.id = transactions.buyer_id AND transactions.status = 'completed'"
                    )
                ],
                group_by="users.id, users.username, users.email",
                order_by="total_amount DESC",
                page=1,
                page_size=20
            )
        ),
        QueryTemplate(
            name="冲突详情（含处理人）",
            description="查询冲突记录，包括处理人信息",
            request=QueryRequest(
                base_table="conflict_records",
                columns=[
                    ColumnConfig(name="id", table="conflict_records"),
                    ColumnConfig(name="table_name", table="conflict_records"),
                    ColumnConfig(name="record_id", table="conflict_records"),
                    ColumnConfig(name="source_db", table="conflict_records"),
                    ColumnConfig(name="target_db", table="conflict_records"),
                    ColumnConfig(name="conflict_type", table="conflict_records"),
                    ColumnConfig(name="resolved", table="conflict_records"),
                    ColumnConfig(name="username", table="users", alias="resolver_name"),
                    ColumnConfig(name="resolved_at", table="conflict_records"),
                    ColumnConfig(name="created_at", table="conflict_records")
                ],
                joins=[
                    JoinConfig(
                        table="users",
                        type="LEFT",
                        on="conflict_records.resolved_by = users.id"
                    )
                ],
                where="conflict_records.resolved = 1",
                order_by="conflict_records.resolved_at DESC",
                page=1,
                page_size=20
            )
        ),
        QueryTemplate(
            name="热门商品排行",
            description="按浏览量统计热门商品",
            request=QueryRequest(
                base_table="items",
                columns=[
                    ColumnConfig(name="id", table="items"),
                    ColumnConfig(name="title", table="items"),
                    ColumnConfig(name="price", table="items"),
                    ColumnConfig(name="username", table="users", alias="seller_name"),
                    ColumnConfig(name="COUNT(user_activities.id)", alias="view_count")
                ],
                joins=[
                    JoinConfig(table="users", on="items.seller_id = users.id"),
                    JoinConfig(
                        table="user_activities",
                        type="LEFT",
                        on="items.id = user_activities.entity_id AND user_activities.entity_type = 'item' AND user_activities.activity_type = 'view_item'"
                    )
                ],
                where="items.status = 'available'",
                group_by="items.id, items.title, items.price, users.username",
                order_by="view_count DESC",
                page=1,
                page_size=20
            )
        ),
        QueryTemplate(
            name="活跃用户分析",
            description="统计用户活跃度（最近7天）",
            request=QueryRequest(
                base_table="users",
                columns=[
                    ColumnConfig(name="id", table="users"),
                    ColumnConfig(name="username", table="users"),
                    ColumnConfig(name="email", table="users"),
                    ColumnConfig(name="COUNT(DISTINCT DATE(user_activities.created_at))", alias="active_days"),
                    ColumnConfig(name="COUNT(user_activities.id)", alias="activity_count")
                ],
                joins=[
                    JoinConfig(
                        table="user_activities",
                        type="LEFT",
                        on="users.id = user_activities.user_id AND user_activities.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
                    )
                ],
                group_by="users.id, users.username, users.email",
                having="activity_count > 0",
                order_by="activity_count DESC",
                page=1,
                page_size=20
            )
        )
    ]
    
    return {"templates": [t.dict() for t in templates]}


@router.get("/tables")
async def get_available_tables(
    _: User = Depends(require_roles("admin"))
) -> Dict[str, List[str]]:
    """获取可查询的表列表"""
    return {"tables": sorted(list(ALLOWED_TABLES))}
