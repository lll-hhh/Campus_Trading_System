"""Administrative data table management APIs."""
from __future__ import annotations

import csv
import datetime as dt
import io
import json
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import MetaData, Table, and_, func, or_, select
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_db_session, require_roles

router = APIRouter(
    prefix="/admin/tables",
    tags=["Admin Tables"],
    dependencies=[Depends(require_roles("admin", "market_admin"))],
)

# 与前端 AdminTablesView 对齐的白名单
ALLOWED_TABLES: Dict[str, str] = {
    "users": "users",
    "categories": "categories",
    "items": "items",
    "item_images": "item_images",
    "comments": "comments",
    "transactions": "transactions",
    "messages": "messages",
    "favorites": "favorites",
    "reports": "reports",
    "audit_logs": "audit_logs",
    "conflict_records": "conflict_records",
    "daily_stats": "daily_stats",
    "system_configs": "system_configs",
    "user_follows": "user_follows",
    "item_view_history": "item_view_history",
    "user_addresses": "user_addresses",
    "item_price_history": "item_price_history",
    "comment_likes": "comment_likes",
    "message_attachments": "message_attachments",
    "report_actions": "report_actions",
    "transaction_review_images": "transaction_review_images",
    "notifications": "notifications",
    "search_history": "search_history",
    "credit_score_history": "credit_score_history",
    "sync_tasks": "sync_tasks",
    "performance_metrics": "performance_metrics",
    # 扩展数据表
    "user_profiles": "user_profiles",
    "roles": "roles",
    "permissions": "permissions",
    "role_permissions": "role_permissions",
}

SENSITIVE_COLUMNS = {"password_hash", "hashed_password", "token"}
MAX_EXPORT_ROWS = 5000


class BatchDeleteRequest(BaseModel):
    """Payload for batch delete endpoint."""

    ids: List[int] = Field(..., min_items=1, max_items=1000)


def _get_table(table_name: str, session: Session) -> Table:
    actual_name = ALLOWED_TABLES.get(table_name)
    if actual_name is None:
        raise HTTPException(status_code=404, detail="不支持的表名")

    metadata = MetaData()
    try:
        table = Table(actual_name, metadata, autoload_with=session.get_bind())
    except Exception as exc:  # pragma: no cover - 依赖数据库元数据
        raise HTTPException(status_code=404, detail=f"表 {actual_name} 不存在: {exc}") from exc
    return table


def _coerce_datetime(value: Any) -> dt.datetime:
    if isinstance(value, (int, float)):
        # Naive UI 返回的是毫秒时间戳
        timestamp = value / 1000 if value > 1_000_000_000_000 else value
        return dt.datetime.fromtimestamp(timestamp)
    if isinstance(value, str):
        try:
            return dt.datetime.fromisoformat(value)
        except ValueError:
            pass
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        return dt.datetime.combine(value, dt.time())
    if isinstance(value, dt.datetime):
        return value
    raise ValueError("无法解析日期时间值")


def _coerce_value(column, value: Any) -> Any:
    try:
        python_type = column.type.python_type  # type: ignore[attr-defined]
    except (NotImplementedError, AttributeError):
        python_type = None

    if value is None or python_type is None:
        return value

    if python_type is bool:
        if isinstance(value, str):
            return value.lower() == "true"
        return bool(value)

    if python_type in (int, float, Decimal):
        if isinstance(value, list):
            return [python_type(v) for v in value]
        return python_type(value)

    if python_type in (dt.date, dt.datetime):
        if isinstance(value, list):
            return [_coerce_datetime(v) for v in value]
        return _coerce_datetime(value)

    return value


def _build_single_condition(column, operator: str, value: Any):
    """Build a single SQLAlchemy filter expression from operator and value.

    Supports:
    - String: eq, ne, contains, notContains, startsWith, endsWith, isEmpty, isNotEmpty
    - Number: eq, ne, gt, gte, lt, lte, between, notBetween, in, notIn
    - Date: eq, gt (after), lt (before), between, last7days, last30days, last90days, today, thisWeek, thisMonth
    - Enum: eq, ne, in, notIn
    - Boolean: true, false, eq
    """
    operator = (operator or "eq").lower()

    # --- 空值检查 ---
    if operator in {"isempty", "is_empty"}:
        return or_(column.is_(None), column == "")
    if operator in {"isnotempty", "is_not_empty"}:
        return and_(column.is_not(None), column != "")

    # --- 日期快捷运算符 ---
    if operator in {"last7days", "last30days", "last90days", "today", "thisweek", "thismonth"}:
        now = dt.datetime.now()
        if operator == "today":
            start = dt.datetime(now.year, now.month, now.day)
            end = start + dt.timedelta(days=1)
            return and_(column >= start, column < end)
        elif operator == "thisweek":
            start = dt.datetime(now.year, now.month, now.day) - dt.timedelta(days=now.weekday())
            return column >= start
        elif operator == "thismonth":
            start = dt.datetime(now.year, now.month, 1)
            return column >= start
        elif operator == "last7days":
            start = now - dt.timedelta(days=7)
            return column >= start
        elif operator == "last30days":
            start = now - dt.timedelta(days=30)
            return column >= start
        else:  # last90days
            start = now - dt.timedelta(days=90)
            return column >= start

    # --- 布尔运算符 ---
    if operator in {"true", "false"}:
        bool_val = operator == "true"
        return column.is_(bool_val)

    # --- 日期比较别名 ---
    if operator == "after":
        operator = "gt"
    if operator == "before":
        operator = "lt"

    coerced = _coerce_value(column, value)

    # --- 基本比较 ---
    if operator == "eq":
        return column == coerced
    if operator == "ne":
        return column != coerced
    if operator == "gt":
        return column > coerced
    if operator == "gte":
        return column >= coerced
    if operator == "lt":
        return column < coerced
    if operator == "lte":
        return column <= coerced

    # --- 字符串运算符 ---
    if operator == "contains" and isinstance(coerced, str):
        return column.ilike(f"%{coerced}%")
    if operator == "notcontains" and isinstance(coerced, str):
        return column.notilike(f"%{coerced}%")
    if operator == "startswith" and isinstance(coerced, str):
        return column.ilike(f"{coerced}%")
    if operator == "endswith" and isinstance(coerced, str):
        return column.ilike(f"%{coerced}")

    # --- 范围运算符 ---
    if operator == "between" and isinstance(coerced, (list, tuple)) and len(coerced) == 2:
        return column.between(coerced[0], coerced[1])
    if operator == "notbetween" and isinstance(coerced, (list, tuple)) and len(coerced) == 2:
        return ~column.between(coerced[0], coerced[1])

    # --- 集合运算符 ---
    if operator == "in":
        if isinstance(coerced, (list, tuple)):
            return column.in_(coerced)
        return column == coerced  # 单值当作等于
    if operator == "notin":
        if isinstance(coerced, (list, tuple)):
            return column.not_in(coerced)
        return column != coerced

    return None


def _build_filters(table: Table, raw_filters: Optional[str]):
    if not raw_filters:
        return None
    try:
        filters = json.loads(raw_filters)
        if not isinstance(filters, list):
            return None
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="filters 参数格式不正确")

    expression = None
    for condition in filters:
        field = condition.get("field")
        operator = condition.get("operator", "eq")
        column = table.c.get(field)
        if column is None:
            continue
        value = condition.get("value")
        single = _build_single_condition(column, operator, value)
        if single is None:
            continue
        if expression is None:
            expression = single
        else:
            logic = str(condition.get("logic", "AND")).upper()
            if logic == "OR":
                expression = or_(expression, single)
            else:
                expression = and_(expression, single)
    return expression


def _serialize_value(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _serialize_row(row, column_names: Iterable[str]) -> Dict[str, Any]:
    data = {}
    mapping = row._mapping  # RowMapping
    for column in column_names:
        if column in SENSITIVE_COLUMNS:
            continue
        data[column] = _serialize_value(mapping.get(column))
    return data


@router.get("/{table_name}")
def list_table_records(
    table_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("desc", pattern="^(?i)(asc|desc)$"),
    filters: Optional[str] = Query(None, description="JSON 字符串数组"),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    table = _get_table(table_name, session)
    filter_expr = _build_filters(table, filters)

    query = select(table)
    if filter_expr is not None:
        query = query.where(filter_expr)

    column = table.c.get(sort_by or "id")
    if column is None:
        column = table.c.id if "id" in table.c else None
    if column is not None:
        query = query.order_by(column.asc() if sort_order.lower() == "asc" else column.desc())

    total_query = select(func.count()).select_from(table)
    if filter_expr is not None:
        total_query = total_query.where(filter_expr)
    total = session.execute(total_query).scalar_one()

    offset = (page - 1) * page_size
    rows = session.execute(query.offset(offset).limit(page_size)).all()
    column_names = [col.name for col in table.columns]
    items = [_serialize_row(row, column_names) for row in rows]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.delete("/{table_name}/{record_id}")
def delete_record(
    table_name: str,
    record_id: int,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    table = _get_table(table_name, session)
    if "id" not in table.c:
        raise HTTPException(status_code=400, detail="该表不支持按 ID 删除")

    result = session.execute(table.delete().where(table.c.id == record_id))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"deleted": result.rowcount}


@router.post("/{table_name}/batch-delete")
def batch_delete_records(
    table_name: str,
    payload: BatchDeleteRequest,
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    table = _get_table(table_name, session)
    if "id" not in table.c:
        raise HTTPException(status_code=400, detail="该表不支持按 ID 删除")

    result = session.execute(table.delete().where(table.c.id.in_(payload.ids)))
    return {"deleted": result.rowcount or 0}


@router.get("/{table_name}/export")
def export_table(
    table_name: str,
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("desc", pattern="^(?i)(asc|desc)$"),
    filters: Optional[str] = Query(None),
    session: Session = Depends(get_db_session),
) -> StreamingResponse:
    table = _get_table(table_name, session)
    filter_expr = _build_filters(table, filters)

    query = select(table)
    if filter_expr is not None:
        query = query.where(filter_expr)

    column = table.c.get(sort_by or "id")
    if column is None and "id" in table.c:
        column = table.c.id
    if column is not None:
        query = query.order_by(column.asc() if sort_order.lower() == "asc" else column.desc())

    query = query.limit(MAX_EXPORT_ROWS)
    result = session.execute(query)
    column_names = [col.name for col in table.columns if col.name not in SENSITIVE_COLUMNS]

    def stream_csv():
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(column_names)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        fetched = 0
        for row in result:
            fetched += 1
            writer.writerow([
                _serialize_value(row._mapping.get(col))
                for col in column_names
            ])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
        if fetched >= MAX_EXPORT_ROWS:
            writer.writerow([f"(仅导出前 {MAX_EXPORT_ROWS} 行)"])
            yield buffer.getvalue()

    filename = f"{table_name}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        stream_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )
