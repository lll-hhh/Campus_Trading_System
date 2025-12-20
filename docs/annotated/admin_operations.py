"""Annotated copy of `backend/apps/api_gateway/routers/admin_operations.py` with per-line comments.
此文件为只读注释版，供 PPT/报告阅读，不用于运行。
"""
from __future__ import annotations  # 注: 启用未来注解语法

import csv  # 注: 用于处理 CSV 文件导入导出
import io  # 注: 用于处理内存中的字节流/字符流
import json  # 注: 用于 JSON 数据序列化与反序列化
import zipfile  # 注: 用于创建 ZIP 压缩包导出
from datetime import datetime, timedelta  # 注: 处理日期时间与时间差
from decimal import Decimal  # 注: 处理高精度数值
from pathlib import Path  # 注: 处理文件路径
from typing import Any, Dict, Iterable, List, Literal  # 注: 类型提示工具

from loguru import logger  # 注: 日志记录器
from fastapi import (  # 注: FastAPI 核心组件
    APIRouter,  # 注: 路由分组
    Depends,  # 注: 依赖注入
    File,  # 注: 文件上传参数
    Form,  # 注: 表单参数
    HTTPException,  # 注: HTTP 异常抛出
    Query,  # 注: 查询参数
    UploadFile,  # 注: 上传文件对象
)
from fastapi.responses import StreamingResponse  # 注: 流式响应，用于文件下载
from pydantic import BaseModel, Field  # 注: Pydantic 模型与字段定义
from sqlalchemy import and_, delete, func, or_, select, text, update  # 注: SQLAlchemy SQL 构建工具
from sqlalchemy.exc import ProgrammingError  # 注: SQL 执行错误异常
from sqlalchemy.orm import Session  # 注: 数据库会话类型

from apps.api_gateway.dependencies import get_db_session, require_roles  # 注: 导入获取 DB 会话和权限检查的依赖
from apps.api_gateway.routers.admin_tables import ALLOWED_TABLES  # 注: 导入允许操作的表名白名单
from apps.core.database import db_manager  # 注: 导入数据库管理器实例
from apps.core.models import (  # 注: 导入所有相关的 ORM 模型
    AuditLog,
    Item,
    Report,
    Role,
    SystemSetting,
    SyncLog,
    Transaction,
    User,
    UserRole,
)
from apps.core.sync_engine import sync_engine  # 注: 导入同步引擎实例
from apps.core.transaction import TransactionConfig  # 注: 导入事务配置
from apps.services.monitoring_simulator import monitoring_data_simulator, query_simulator  # 注: 导入监控数据模拟器
from apps.services.maintenance import MaintenanceTaskRunner  # 注: 导入维护任务运行器

# 注: 创建 API 路由，前缀为 /admin/operations，仅限 admin/market_admin 角色访问
router = APIRouter(
    prefix="/admin/operations",
    tags=["Admin Operations"],
    dependencies=[Depends(require_roles("admin", "market_admin"))],
)


EXPORT_ROW_LIMIT = 2000  # 注: 导出数据的最大行数限制
IMPORT_ROW_LIMIT = 500  # 注: 导入数据的最大行数限制
SUPPORTED_DATABASES = {"mysql", "mariadb", "postgres", "sqlite"}  # 注: 支持的数据库类型集合
IMPORTABLE_TABLES = {"users", "items", "transactions", "comments", "messages", "audit_logs"}  # 注: 允许导入的表名集合
UPLOAD_DIR = Path("/tmp/campuswap-admin")  # 注: 临时上传目录路径
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # 注: 确保上传目录存在


class BatchUserOperation(BaseModel):  # 注: 定义批量用户操作的请求体模型
    """Payload for batch user instructions."""

    condition: Literal["inactive_30days", "not_verified", "low_credit", "banned"]  # 注: 筛选条件
    action: Literal["delete", "remind", "demote", "reset_credit"]  # 注: 执行动作
    dry_run: bool = False  # 注: 是否仅试运行（不实际修改）


class BatchItemOperation(BaseModel):  # 注: 定义批量商品操作的请求体模型
    """Payload for batch item operations."""

    status: Literal["available", "sold", "deleted", "archived", "all"] = "available"  # 注: 商品状态筛选
    days: int = Field(90, ge=1, le=365)  # 注: 时间范围（天数），限制 1-365
    action: Literal["archive", "delete", "remind_seller"]  # 注: 执行动作
    dry_run: bool = False  # 注: 是否仅试运行


class TransactionCleanupPayload(BaseModel):  # 注: 定义交易清理操作的请求体模型
    """Transaction cleanup instructions."""

    statuses: List[str] = Field(default_factory=list)  # 注: 要清理的交易状态列表
    older_than_days: int = Field(30, ge=1, le=365)  # 注: 清理多少天前的交易


class ExportPayload(BaseModel):  # 注: 定义数据导出请求体模型
    """Data export payload."""

    tables: List[str] = Field(default_factory=list)  # 注: 要导出的表名列表
    format: Literal["json", "csv"] = "json"  # 注: 导出格式
    schedule_only: bool = False  # 注: 是否仅计划任务而不立即下载


class SqlPayload(BaseModel):  # 注: 定义 SQL 执行请求体模型
    """SQL runner payload."""

    database: Literal["mysql", "mariadb", "postgres", "sqlite"] = "mysql"  # 注: 目标数据库
    query: str  # 注: SQL 查询语句
    mode: Literal["run", "explain"] = "run"  # 注: 模式：运行或解释执行计划


class AiAuditPayload(BaseModel):  # 注: 定义 AI 审计开关请求体模型
    """Toggle AI audit mode payload."""

    enabled: bool  # 注: 是否启用


class MaintenanceTaskPayload(BaseModel):  # 注: 定义维护任务请求体模型
    """Payload for system maintenance tasks triggered from the admin panel."""

    task: Literal[  # 注: 具体的维护任务名称枚举
        "cleanup_expired_sessions",
        "cleanup_deleted_records",
        "cleanup_temp_files",
        "vacuum_tables",
        "analyze_indexes",
        "rebuild_indexes",
        "suggest_indexes",
        "optimize_tables",
        "view_audit_logs",
        "export_audit_logs",
        "detect_anomalies",
        "lock_suspicious_users",
        "analyze_slow_queries",
        "cache_warming",
        "adjust_connection_pool",
        "auto_optimize",
        "create_backup",
        "view_backups",
        "restore_backup",
        "schedule_backup",
    ]


def current_admin_user(user: User = Depends(require_roles("admin", "market_admin"))) -> User:  # 注: 依赖函数，获取当前管理员用户
    """Dependency that returns the current admin user."""

    return user  # 注: 返回通过权限检查的用户对象


def _user_condition_expression(condition: str):  # 注: 内部辅助函数，根据条件字符串生成 SQLAlchemy 过滤表达式
    now = datetime.utcnow()  # 注: 获取当前 UTC 时间
    if condition == "inactive_30days":  # 注: 如果条件是 30 天未活跃
        threshold = now - timedelta(days=30)  # 注: 计算 30 天前的阈值
        return or_(User.last_login_at.is_(None), User.last_login_at < threshold)  # 注: 返回未登录或登录时间早于阈值的条件
    if condition == "not_verified":  # 注: 如果条件是未验证
        return User.is_verified.is_(False)  # 注: 返回未验证条件
    if condition == "low_credit":  # 注: 如果条件是低信用分
        return User.credit_score < 60  # 注: 返回信用分小于 60 的条件
    if condition == "banned":  # 注: 如果条件是已封禁
        return User.is_banned.is_(True)  # 注: 返回已封禁条件
    raise HTTPException(status_code=400, detail="不支持的用户筛选条件")  # 注: 抛出不支持的条件异常


def _item_filter_expression(status: str, days: int):  # 注: 内部辅助函数，生成商品过滤表达式
    cutoff = datetime.utcnow() - timedelta(days=days)  # 注: 计算截止时间
    clauses = []  # 注: 初始化条件列表
    if status != "all":  # 注: 如果不是全部状态
        clauses.append(Item.status == status)  # 注: 添加状态过滤
    # 注: 添加时间过滤：更新时间为空、更新时间早于截止时间或创建时间早于截止时间
    clauses.append(or_(Item.updated_at.is_(None), Item.updated_at < cutoff, Item.created_at < cutoff))
    return and_(*clauses)  # 注: 返回所有条件的 AND 组合


def _serialize_value(value: Any) -> Any:  # 注: 内部辅助函数，序列化特殊类型值
    if isinstance(value, datetime):  # 注: 如果是 datetime
        return value.isoformat()  # 注: 转为 ISO 格式字符串
    if isinstance(value, Decimal):  # 注: 如果是 Decimal
        return float(value)  # 注: 转为 float
    return value  # 注: 其他原样返回


def _coerce_table_name(table: str) -> str:  # 注: 内部辅助函数，验证并获取真实表名
    actual = ALLOWED_TABLES.get(table)  # 注: 从白名单映射中获取真实表名
    if not actual:  # 注: 如果不在白名单中
        raise HTTPException(status_code=404, detail=f"表 {table} 不在允许导入/导出列表中")  # 注: 抛出 404 异常
    return actual  # 注: 返回真实表名


def _insert_notifications(session: Session, user_ids: Iterable[int], title: str, content: str) -> None:  # 注: 内部辅助函数，批量插入通知
    rows = [  # 注: 构建插入数据列表
        {
            "user_id": uid,
            "type": "system",
            "title": title,
            "content": content,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        for uid in user_ids
    ]
    if not rows:  # 注: 如果没有数据则返回
        return
    session.execute(  # 注: 执行批量插入 SQL
        text(
            """
            INSERT INTO notifications (user_id, type, title, content, created_at, updated_at)
            VALUES (:user_id, :type, :title, :content, :created_at, :updated_at)
            """
        ),
        rows,
    )


@router.get("/users/estimate")  # 注: 路由：估算符合条件的用户数量
def estimate_users(
    condition: str = Query(..., description="inactive_30days/not_verified/low_credit/banned"),  # 注: 查询参数：筛选条件
    session: Session = Depends(get_db_session),  # 注: 依赖：数据库会话
):
    """Return the number of users that match the batch condition."""

    expr = _user_condition_expression(condition)  # 注: 获取过滤表达式
    count = session.execute(select(func.count()).select_from(User).where(expr)).scalar() or 0  # 注: 执行计数查询
    return {"condition": condition, "count": count}  # 注: 返回结果


@router.post("/users/batch")  # 注: 路由：批量操作用户
def batch_users(
    payload: BatchUserOperation,  # 注: 请求体：批量操作参数
    session: Session = Depends(get_db_session),  # 注: 依赖：数据库会话
    current_user: User = Depends(current_admin_user),  # 注: 依赖：当前管理员
):
    """Execute batch user maintenance commands."""

    expr = _user_condition_expression(payload.condition)  # 注: 获取过滤表达式
    target_ids = (
        session.execute(select(User.id).where(expr).limit(2000)).scalars().all()  # 注: 查询目标用户 ID，限制 2000 条
    )
    if payload.dry_run:  # 注: 如果是试运行
        return {"affected": len(target_ids), "preview": target_ids[:20]}  # 注: 返回影响数量和前 20 个 ID 预览

    if not target_ids:  # 注: 如果没有目标用户
        return {"affected": 0}  # 注: 返回 0

    affected = 0  # 注: 初始化影响行数
    if payload.action == "delete":  # 注: 如果动作是删除
        result = session.execute(
            update(User)
            .where(User.id.in_(target_ids))
            .values(is_active=False, is_banned=True, updated_at=datetime.utcnow())  # 注: 软删除并封禁
        )
        affected = result.rowcount or len(target_ids)  # 注: 记录影响行数
    elif payload.action == "remind":  # 注: 如果动作是提醒
        _insert_notifications(session, target_ids, "账号活跃提醒", "您的账号长期未登录，请及时确认账户安全。")  # 注: 发送通知
        affected = len(target_ids)  # 注: 记录影响行数
    elif payload.action == "demote":  # 注: 如果动作是降级
        role_ids = (
            session.execute(select(Role.id).where(Role.name.in_(["admin", "market_admin"])))  # 注: 查询管理员角色 ID
            .scalars()
            .all()
        )
        if role_ids:
            session.execute(
                delete(UserRole).where(
                    UserRole.user_id.in_(target_ids), UserRole.role_id.in_(role_ids)  # 注: 删除用户的管理员角色关联
                )
            )
        affected = len(target_ids)  # 注: 记录影响行数
    elif payload.action == "reset_credit":  # 注: 如果动作是重置信用分
        result = session.execute(
            update(User)
            .where(User.id.in_(target_ids))
            .values(credit_score=80, updated_at=datetime.utcnow())  # 注: 重置为 80 分
        )
        affected = result.rowcount or len(target_ids)  # 注: 记录影响行数
    else:
        raise HTTPException(status_code=400, detail="不支持的批量操作")  # 注: 抛出异常

    session.add(  # 注: 记录审计日志
        AuditLog(
            actor_id=current_user.id,
            action=f"batch_{payload.action}",
            resource_type="users",
            resource_id=0,
            extra_data={"condition": payload.condition, "affected": affected},
        )
    )
    return {"affected": affected}  # 注: 返回结果


@router.get("/items/estimate")  # 注: 路由：估算符合条件的商品数量
def estimate_items(
    status: str = Query("available"),  # 注: 查询参数：状态
    days: int = Query(90, ge=1, le=365),  # 注: 查询参数：天数
    session: Session = Depends(get_db_session),  # 注: 依赖：数据库会话
):
    """Return the estimated number of items affected."""

    expr = _item_filter_expression(status, days)  # 注: 获取过滤表达式
    count = session.execute(select(func.count()).select_from(Item).where(expr)).scalar() or 0  # 注: 执行计数查询
    return {"status": status, "days": days, "count": count}  # 注: 返回结果


@router.post("/items/batch")  # 注: 路由：批量操作商品
def batch_items(
    payload: BatchItemOperation,  # 注: 请求体
    session: Session = Depends(get_db_session),  # 注: 依赖：数据库会话
    current_user: User = Depends(current_admin_user),  # 注: 依赖：当前管理员
):
    """Execute batch actions on items."""

    expr = _item_filter_expression(payload.status, payload.days)  # 注: 获取过滤表达式
    item_ids = (
        session.execute(select(Item.id).where(expr).limit(2000)).scalars().all()  # 注: 查询目标商品 ID
    )
    if payload.dry_run:  # 注: 试运行
        return {"affected": len(item_ids), "preview": item_ids[:20]}
    if not item_ids:
        return {"affected": 0}

    affected = 0
    if payload.action == "archive":  # 注: 归档操作
        result = session.execute(
            update(Item)
            .where(Item.id.in_(item_ids))
            .values(status="archived", updated_at=datetime.utcnow())  # 注: 更新状态为 archived
        )
        affected = result.rowcount or len(item_ids)
    elif payload.action == "delete":  # 注: 删除操作
        result = session.execute(
            update(Item)
            .where(Item.id.in_(item_ids))
            .values(status="deleted", updated_at=datetime.utcnow())  # 注: 更新状态为 deleted
        )
        affected = result.rowcount or len(item_ids)
    elif payload.action == "remind_seller":  # 注: 提醒卖家操作
        seller_ids = (
            session.execute(select(Item.seller_id).where(Item.id.in_(item_ids))).scalars().all()  # 注: 查询卖家 ID
        )
        _insert_notifications(  # 注: 发送通知
            session,
            seller_ids,
            "商品下架提醒",
            "您的商品长时间未更新状态，请确认是否仍需上架。",
        )
        affected = len(seller_ids)
    else:
        raise HTTPException(status_code=400, detail="不支持的批量商品操作")

    session.add(  # 注: 记录审计日志
        AuditLog(
            actor_id=current_user.id,
            action=f"item_{payload.action}",
            resource_type="items",
            resource_id=0,
            extra_data={"status": payload.status, "days": payload.days, "affected": affected},
        )
    )
    return {"affected": affected}


@router.post("/transactions/cleanup")  # 注: 路由：清理交易
def cleanup_transactions(
    payload: TransactionCleanupPayload,  # 注: 请求体
    session: Session = Depends(get_db_session),  # 注: 依赖：数据库会话
    current_user: User = Depends(current_admin_user),  # 注: 依赖：当前管理员
):
    """Cleanup stale transactions by marking them cancelled."""

    statuses = payload.statuses or ["pending", "cancelled", "timeout"]  # 注: 默认清理状态
    cutoff = datetime.utcnow() - timedelta(days=payload.older_than_days)  # 注: 计算截止时间
    stmt = (
        update(Transaction)
        .where(Transaction.status.in_(statuses))  # 注: 匹配状态
        .where(or_(Transaction.updated_at.is_(None), Transaction.updated_at < cutoff))  # 注: 匹配时间
        .values(status="cancelled", cancelled_at=datetime.utcnow())  # 注: 标记为已取消
    )
    result = session.execute(stmt)  # 注: 执行更新
    affected = result.rowcount or 0  # 注: 获取影响行数
    session.add(  # 注: 记录审计日志
        AuditLog(
            actor_id=current_user.id,
            action="transaction_cleanup",
            resource_type="transactions",
            resource_id=0,
            extra_data={"statuses": statuses, "affected": affected},
        )
    )
    return {"affected": affected}


def _serialize_rows(rows: Iterable[Any]) -> List[Dict[str, Any]]:  # 注: 内部辅助函数，序列化多行数据
    serialized: List[Dict[str, Any]] = []
    for row in rows:
        mapping = row._mapping if hasattr(row, "_mapping") else row  # 注: 获取字典映射
        serialized.append({key: _serialize_value(value) for key, value in dict(mapping).items()})  # 注: 序列化每一列
    return serialized


def _build_export_archive(session: Session, tables: List[str], fmt: str) -> io.BytesIO:  # 注: 内部辅助函数，构建导出压缩包
    buffer = io.BytesIO()  # 注: 创建内存缓冲区
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:  # 注: 创建 ZIP 文件
        for table in tables:
            actual = _coerce_table_name(table)  # 注: 获取真实表名
            result = session.execute(text(f"SELECT * FROM {actual} LIMIT :limit"), {"limit": EXPORT_ROW_LIMIT})  # 注: 查询数据
            rows = _serialize_rows(result)  # 注: 序列化数据
            filename = f"{actual}.{fmt}"  # 注: 生成文件名
            if fmt == "json":  # 注: JSON 格式
                payload = json.dumps(rows, ensure_ascii=False, indent=2)
            else:  # 注: CSV 格式
                csv_buffer = io.StringIO()
                writer = None
                for row in rows:
                    if writer is None:
                        writer = csv.DictWriter(csv_buffer, fieldnames=list(row.keys()))
                        writer.writeheader()
                    writer.writerow(row)
                payload = csv_buffer.getvalue()
            archive.writestr(filename, payload)  # 注: 写入 ZIP
    buffer.seek(0)  # 注: 重置指针
    return buffer


@router.post("/export")  # 注: 路由：导出数据
def export_tables(
    payload: ExportPayload,  # 注: 请求体
    session: Session = Depends(get_db_session),  # 注: 依赖：数据库会话
    current_user: User = Depends(current_admin_user),  # 注: 依赖：当前管理员
):
    """Export whitelisted tables into a zipped archive."""

    if not payload.tables:
        raise HTTPException(status_code=400, detail="请选择至少一个数据表")

    unique_tables = sorted({table for table in payload.tables})  # 注: 去重并排序
    if payload.schedule_only:  # 注: 如果仅计划任务
        session.add(  # 注: 记录审计日志
            AuditLog(
                actor_id=current_user.id,
                action="export_schedule",
                resource_type="tables",
                resource_id=0,
                extra_data={"tables": unique_tables, "format": payload.format},
            )
        )
        return {"scheduled": True, "tables": unique_tables}

    archive = _build_export_archive(session, unique_tables, payload.format)  # 注: 构建压缩包
    filename = f"campuswap-export-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.zip"  # 注: 生成文件名
    headers = {"Content-Disposition": f"attachment; filename={filename}"}  # 注: 设置下载头
    return StreamingResponse(archive, media_type="application/zip", headers=headers)  # 注: 返回流式响应


async def _load_import_rows(file: UploadFile) -> List[Dict[str, Any]]:  # 注: 内部辅助函数，加载导入文件数据
    suffix = (Path(file.filename or "").suffix or "").lower()  # 注: 获取文件后缀
    raw = await file.read()  # 注: 读取文件内容
    if suffix == ".json":  # 注: JSON 文件
        data = json.loads(raw.decode("utf-8"))
        if isinstance(data, dict) and "items" in data:
            rows = data["items"]
        elif isinstance(data, list):
            rows = data
        else:
            raise HTTPException(status_code=400, detail="JSON 结构无法识别")
    elif suffix == ".csv":  # 注: CSV 文件
        text_data = raw.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text_data))
        rows = list(reader)
    elif suffix == ".sql":  # 注: SQL 文件
        target = UPLOAD_DIR / f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{file.filename}"
        target.write_bytes(raw)  # 注: 保存到临时目录
        return []  # 注: SQL 文件不直接解析返回行
    else:
        raise HTTPException(status_code=400, detail="仅支持 JSON/CSV/SQL 文件")
    if len(rows) > IMPORT_ROW_LIMIT:  # 注: 检查行数限制
        raise HTTPException(status_code=400, detail=f"单次导入最多 {IMPORT_ROW_LIMIT} 行")
    return rows


@router.post("/import")  # 注: 路由：导入数据
async def import_table(
    table: str = Form(...),  # 注: 表单参数：表名
    mode: Literal["replace", "append", "update"] = Form("append"),  # 注: 表单参数：模式
    file: UploadFile = File(...),  # 注: 文件上传
    session: Session = Depends(get_db_session),  # 注: 依赖：数据库会话
    current_user: User = Depends(current_admin_user),  # 注: 依赖：当前管理员
):
    """Import structured data into allowed tables."""

    actual = _coerce_table_name(table)  # 注: 验证表名
    if actual not in IMPORTABLE_TABLES:
        raise HTTPException(status_code=400, detail="该表暂不支持后台导入")

    rows = await _load_import_rows(file)  # 注: 加载数据
    if not rows:
        return {"stored": True, "message": "SQL 文件已保存，请使用手动脚本执行"}

    if mode == "replace":  # 注: 替换模式，先清空表
        session.execute(text(f"DELETE FROM {actual}"))

    inserted = 0
    for row in rows:
        clean_row = {key: value for key, value in row.items() if value not in (None, "")}  # 注: 清理空值
        if mode == "update" and "id" in clean_row:  # 注: 更新模式
            stmt = (
                update(text(actual))
                .where(text(f"{actual}.id = :id"))
                .values(**clean_row)
            )
            session.execute(stmt, clean_row)
        else:  # 注: 插入模式
            columns = ", ".join(clean_row.keys())
            placeholders = ", ".join([f":{key}" for key in clean_row.keys()])
            session.execute(text(f"INSERT INTO {actual} ({columns}) VALUES ({placeholders})"), clean_row)
        inserted += 1

    session.add(  # 注: 记录审计日志
        AuditLog(
            actor_id=current_user.id,
            action="import",
            resource_type=actual,
            resource_id=0,
            extra_data={"rows": inserted, "mode": mode},
        )
    )
    return {"imported": inserted, "table": actual}


def _assert_safe_sql(query: str) -> None:  # 注: 内部辅助函数，检查 SQL 安全性
    lowered = query.strip().lower()
    if not lowered:
        raise HTTPException(status_code=400, detail="SQL 语句不能为空")
    allowed_prefixes = ("select", "with", "show", "explain", "desc", "pragma")  # 注: 允许的起始关键字
    if not lowered.startswith(allowed_prefixes):
        raise HTTPException(status_code=400, detail="仅允许只读 SQL 语句")
    banned_tokens = ("drop ", "delete ", "truncate ", "update ", "insert ", "alter ", "create ")  # 注: 禁止的关键字
    if any(token in lowered for token in banned_tokens):
        raise HTTPException(status_code=400, detail="SQL 包含危险操作")


@router.post("/sql")  # 注: 路由：执行 SQL
def run_sql(
    payload: SqlPayload,  # 注: 请求体
    session: Session = Depends(get_db_session),  # 注: 依赖：数据库会话
    current_user: User = Depends(current_admin_user),  # 注: 依赖：当前管理员
):
    """Execute a read-only SQL query against a chosen database."""

    _assert_safe_sql(payload.query)  # 注: 安全检查
    if payload.database not in SUPPORTED_DATABASES:
        raise HTTPException(status_code=400, detail="不支持的数据库类型")

    with db_manager.session_scope(payload.database) as session:  # 注: 使用指定数据库的会话
        started = datetime.utcnow()
        try:
            statement = payload.query if payload.mode == "run" else f"EXPLAIN {payload.query}"  # 注: 构建语句
            result = session.execute(text(statement))  # 注: 执行
            rows = _serialize_rows(result.fetchmany(200))  # 注: 获取前 200 行
        except ProgrammingError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    duration = (datetime.utcnow() - started).total_seconds() * 1000  # 注: 计算耗时
    session.add(  # 注: 记录审计日志
        AuditLog(
            actor_id=current_user.id,
            action="sql_runner",
            resource_type=payload.database,
            resource_id=0,
            extra_data={"query": payload.query[:200], "duration_ms": duration},
        )
    )
    return {"rows": rows, "rowcount": len(rows), "duration_ms": round(duration, 2)}


def _collect_running_queries(limit: int = 10) -> List[Dict[str, Any]]:  # 注: 内部辅助函数，收集正在运行的查询
    running: List[Dict[str, Any]] = []
    try:
        with db_manager.session_scope("mysql") as session:  # 注: 连接 MySQL
            rows = session.execute(text("SHOW FULL PROCESSLIST")).mappings().all()  # 注: 执行 SHOW PROCESSLIST
        for row in rows:
            command = (row.get("Command") or "").lower()
            if command in {"sleep", "binlog dump"}:  # 注: 忽略休眠和复制进程
                continue
            running.append(
                {
                    "id": str(row.get("Id")),
                    "database": row.get("db") or "mysql",
                    "query": row.get("Info") or "",
                    "status": row.get("State") or row.get("Command"),
                    "duration": int(row.get("Time") or 0) * 1000,
                }
            )
            if len(running) >= limit:
                break
    except Exception as exc:  # pragma: no cover - SHOW PROCESSLIST may need privileges
        logger.warning("Failed to read process list: %s", exc)
    if len(running) < limit:
        running.extend(query_simulator.snapshot(limit - len(running)))  # 注: 如果不足，使用模拟数据补充
    return running[:limit]


def _pool_snapshot(running_queries: List[Dict[str, Any]]):  # 注: 内部辅助函数，生成连接池快照
    active = len(running_queries)
    max_pool = TransactionConfig.POOL_SIZE
    usage = min(100, int((active / max_pool) * 100)) if max_pool else 0
    idle = max(max_pool - active, 0)
    return {
        "active": active,
        "idle": idle,
        "max": max_pool,
        "waiting": max(active - max_pool, 0),
        "timeouts": 0,
        "usage": usage,
    }


@router.get("/performance/insights")  # 注: 路由：获取性能洞察数据
def performance_insights(session: Session = Depends(get_db_session)):
    """Return aggregated monitoring data for AdminPerformanceView."""

    monitoring_data_simulator.ensure_baseline()  # 注: 确保有基准监控数据
    running_queries = _collect_running_queries()  # 注: 收集运行中查询
    pool = _pool_snapshot(running_queries)  # 注: 获取连接池状态

    slow_queries: List[Dict[str, Any]] = []
    try:
        rows = session.execute(  # 注: 查询慢查询指标
            text(
                """
                SELECT id, db_name, metric_value, details, recorded_at
                FROM performance_metrics
                WHERE metric_type IN ('query_time', 'query_time_avg')
                ORDER BY recorded_at DESC
                LIMIT 10
                """
            )
        ).mappings().all()
        for row in rows:
            details = row.get("details") or {}
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except json.JSONDecodeError:
                    details = {}
            slow_queries.append(
                {
                    "id": f"Q{row['id']}",
                    "sql": details.get("sql") or f"SELECT * FROM {details.get('table', 'items')} LIMIT 50",
                    "count": details.get("count", 1),
                    "avgTime": float(row.get("metric_value") or 0),
                    "maxTime": float(details.get("max_time") or row.get("metric_value") or 0),
                    "rows": details.get("rows", 0),
                    "suggestion": details.get("suggestion") or "考虑为过滤列添加复合索引",
                }
            )
    except ProgrammingError:
        pass

    if not slow_queries:  # 注: 如果没有慢查询，使用模拟数据
        slow_queries = [
            {
                "id": "Q-items",
                "sql": "SELECT * FROM items WHERE status = 'available' ORDER BY updated_at DESC",
                "count": 120,
                "avgTime": 85,
                "maxTime": 230,
                "rows": 200,
                "suggestion": "为 status, updated_at 添加组合索引",
            }
        ]

    recent_window = datetime.utcnow() - timedelta(minutes=5)
    sync_events = (
        session.execute(select(func.count()).select_from(SyncLog).where(SyncLog.started_at >= recent_window)).scalar()
        or 0
    )
    qps = round(sync_events / (5 * 60), 2)  # 注: 计算 QPS
    avg_query_time = round(
        (sum(item["avgTime"] for item in slow_queries) / len(slow_queries)) if slow_queries else 12.0,
        2,
    )

    unresolved_conflicts = session.execute(
        text("SELECT COUNT(*) FROM conflict_records WHERE resolved = 0")
    ).scalar() or 0
    total_conflicts = session.execute(text("SELECT COUNT(*) FROM conflict_records")).scalar() or 1
    conflict_ratio = unresolved_conflicts / max(total_conflicts, 1)

    # 注: 计算各项健康指标得分
    db_connection = max(50, 100 - max(pool["usage"] - 50, 0))
    query_speed = max(40, 100 - avg_query_time)
    sync_consistency = max(60, int((1 - conflict_ratio) * 100))
    resource_usage = min(95, pool["usage"] + 5)
    system_health = round(
        db_connection * 0.3
        + query_speed * 0.3
        + sync_consistency * 0.3
        + (100 - resource_usage) * 0.1,
        2,
    )

    connection_pools = {  # 注: 构建各数据库连接池状态
        "mysql": pool,
        "postgres": {**pool, "usage": max(pool["usage"] - 10, 5)},
        "mariadb": {**pool, "usage": max(pool["usage"] - 5, 5)},
        "sqlite": {**pool, "max": 1, "active": min(pool["active"], 1), "idle": 0, "usage": min(pool["usage"], 100)},
    }

    health = {  # 注: 构建健康状态对象
        "dbConnection": int(db_connection),
        "querySpeed": int(query_speed),
        "syncConsistency": int(sync_consistency),
        "resourceUsage": int(resource_usage),
        "score": system_health,
    }

    return {
        "slow_queries": slow_queries,
        "running_queries": running_queries,
        "connection_pools": connection_pools,
        "health": health,
        "stats": {"avg_query_time": avg_query_time, "qps": qps},
    }


@router.get("/performance/heatmap")  # 注: 路由：获取热力图数据
def performance_heatmap(days: int = Query(7, ge=1, le=14)):
    """Return recent sync activity heatmap data for analytics dashboards."""

    monitoring_data_simulator.ensure_baseline()
    data = monitoring_data_simulator.generate_heatmap(days)  # 注: 生成热力图数据
    return {"days": days, "data": data}


@router.post("/databases/{db_name}/sync")  # 注: 路由：触发单个数据库同步
def sync_single_database(db_name: str, current_user: User = Depends(current_admin_user)):
    """Trigger a manual sync run and tag the requested target."""

    if db_name not in SUPPORTED_DATABASES:
        raise HTTPException(status_code=404, detail="未知的数据库标识")
    sync_engine.run_periodic_sync()  # 注: 调用同步引擎
    return {"scheduled": True, "target": db_name}


@router.post("/maintenance")  # 注: 路由：触发维护任务
def trigger_maintenance_task(
    payload: MaintenanceTaskPayload,  # 注: 请求体
    session: Session = Depends(get_db_session),  # 注: 依赖：数据库会话
    current_user: User = Depends(current_admin_user),  # 注: 依赖：当前管理员
):
    """Execute a maintenance task and record it as an audit event."""

    runner = MaintenanceTaskRunner(session)  # 注: 实例化维护任务运行器
    try:
        result = runner.run(payload.task)  # 注: 运行任务
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    session.add(  # 注: 记录审计日志
        AuditLog(
            actor_id=current_user.id,
            action="maintenance_task",
            resource_type="maintenance",
            resource_id=result.get("job_id", 0),
            extra_data={
                "task": payload.task,
                "job_id": result.get("job_id"),
                "affected_rows": result.get("affected_rows", 0),
                "message": result.get("message", ""),
            },
        )
    )
    return result


@router.get("/databases/{db_name}")  # 注: 路由：获取数据库详情（同步日志）
def database_details(db_name: str, session: Session = Depends(get_db_session)):
    """Return last few sync logs for a database target."""

    if db_name not in SUPPORTED_DATABASES:
        raise HTTPException(status_code=404, detail="未知的数据库标识")
    rows = session.execute(  # 注: 查询最近的同步日志
        text(
            """
            SELECT id, status, started_at, completed_at, stats
            FROM sync_logs
            WHERE JSON_UNQUOTE(JSON_EXTRACT(stats, '$.target')) = :target
            ORDER BY started_at DESC
            LIMIT 5
            """
        ),
        {"target": db_name},
    ).mappings().all()
    logs: List[Dict[str, Any]] = []
    for row in rows:
        stats = row.get("stats") or {}
        if isinstance(stats, str):
            try:
                stats = json.loads(stats)
            except json.JSONDecodeError:
                stats = {}
        logs.append(
            {
                "id": row["id"],
                "status": row["status"],
                "started_at": _serialize_value(row.get("started_at")),
                "completed_at": _serialize_value(row.get("completed_at")),
                "mode": stats.get("mode"),
            }
        )
    return {"database": db_name, "logs": logs}


@router.post("/queries/{query_id}/kill")  # 注: 路由：终止查询
def kill_query(query_id: str, current_user: User = Depends(current_admin_user)):
    """Kill a running MySQL query."""

    try:
        numeric_id = int(query_id)
    except ValueError:
        numeric_id = None

    if numeric_id is not None:
        try:
            with db_manager.session_scope("mysql") as session:  # 注: 连接 MySQL
                session.execute(text(f"KILL {numeric_id}"))  # 注: 执行 KILL 命令
            return {"killed": numeric_id, "simulated": False}
        except Exception as exc:  # pragma: no cover - depends on DB privileges
            logger.warning("Failed to kill query %s: %s", query_id, exc)

    if query_simulator.kill(query_id):  # 注: 尝试终止模拟查询
        return {"killed": query_id, "simulated": True}

    raise HTTPException(status_code=404, detail="未找到正在运行的查询")


@router.post("/sync/replay")  # 注: 路由：重放同步事件
def replay_stalled_events(session: Session = Depends(get_db_session), current_user: User = Depends(current_admin_user)):
    """Replay latest failed sync events by scheduling a new run."""

    failed = session.execute(  # 注: 查询失败的同步日志
        text("SELECT id FROM sync_logs WHERE status = 'failed' ORDER BY started_at DESC LIMIT 20")
    ).fetchall()
    sync_engine.run_periodic_sync()  # 注: 触发同步
    session.add(  # 注: 记录审计日志
        AuditLog(
            actor_id=current_user.id,
            action="sync_replay",
            resource_type="sync",
            resource_id=0,
            extra_data={"failed": len(failed)},
        )
    )
    return {"replayed": len(failed)}


@router.get("/conflicts/export")  # 注: 路由：导出冲突记录
def export_conflicts(session: Session = Depends(get_db_session)):
    """Export conflict records into a CSV file."""

    rows = session.execute(  # 注: 查询冲突记录
        text(
            """
            SELECT id, table_name, record_id, source_db, target_db, conflict_type, created_at, resolution_strategy
            FROM conflict_records
            ORDER BY created_at DESC
            LIMIT 1000
            """
        )
    ).fetchall()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "table", "record_id", "source", "target", "type", "created_at", "strategy"])  # 注: 写入表头
    for row in rows:
        writer.writerow(row)  # 注: 写入行
    buffer.seek(0)
    filename = f"conflicts-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(io.BytesIO(buffer.getvalue().encode("utf-8")), media_type="text/csv", headers=headers)


@router.get("/ai/audit-mode")  # 注: 路由：获取 AI 审计模式状态
def get_ai_audit_mode(session: Session = Depends(get_db_session)):
    setting = session.execute(  # 注: 查询系统设置
        select(SystemSetting).where(SystemSetting.category == "ai", SystemSetting.key == "audit_mode")
    ).scalar_one_or_none()
    enabled = bool((setting.value or {}).get("enabled")) if setting else False
    return {"enabled": enabled, "updated_at": _serialize_value(setting.updated_at) if setting else None}


@router.post("/ai/audit-mode")  # 注: 路由：更新 AI 审计模式状态
def update_ai_audit_mode(
    payload: AiAuditPayload,  # 注: 请求体
    session: Session = Depends(get_db_session),  # 注: 依赖：数据库会话
    current_user: User = Depends(current_admin_user),  # 注: 依赖：当前管理员
):
    setting = session.execute(  # 注: 查询系统设置
        select(SystemSetting).where(SystemSetting.category == "ai", SystemSetting.key == "audit_mode")
    ).scalar_one_or_none()
    value = {"enabled": payload.enabled, "updated_by": current_user.username, "updated_at": datetime.utcnow().isoformat()}
    if setting:  # 注: 如果存在则更新
        setting.value = value
        setting.updated_by = current_user.id
    else:  # 注: 如果不存在则创建
        setting = SystemSetting(category="ai", key="audit_mode", value=value, updated_by=current_user.id)
        session.add(setting)
    return {"enabled": payload.enabled}


@router.get("/profile/insights")  # 注: 路由：获取管理员概览数据
def profile_insights(
    session: Session = Depends(get_db_session),  # 注: 依赖：数据库会话
    current_user: User = Depends(current_admin_user),  # 注: 依赖：当前管理员
):
    """Expose aggregated profile data for AdminProfileView."""

    last_audit = session.execute(  # 注: 查询最后一次审计日志
        select(AuditLog)
        .where(AuditLog.actor_id == current_user.id)
        .order_by(AuditLog.created_at.desc())
    ).scalars().first()
    pending_reports = session.execute(  # 注: 查询待处理举报数量
        select(func.count()).select_from(Report).where(Report.status == "pending")
    ).scalar() or 0
    unresolved_conflicts = session.execute(  # 注: 查询未解决冲突数量
        text("SELECT COUNT(*) FROM conflict_records WHERE resolved = 0")
    ).scalar() or 0

    security_tips = []  # 注: 生成安全提示
    if pending_reports:
        security_tips.append(f"有 {pending_reports} 条举报待处理，请尽快跟进。")
    else:
        security_tips.append("当前没有待处理举报，可专注于交易质量。")
    if unresolved_conflicts:
        security_tips.append(f"同步模块存在 {unresolved_conflicts} 条待解决冲突，建议优先处理。")
    else:
        security_tips.append("同步冲突已全部处理，保持监控即可。")

    recent_actions = []
    if last_audit:
        recent_actions.append(
            {
                "action": last_audit.action,
                "resource": last_audit.resource_type,
                "time": _serialize_value(last_audit.created_at),
            }
        )

    return {
        "lastLoginAt": _serialize_value(current_user.last_login_at) if current_user.last_login_at else None,
        "pendingReports": pending_reports,
        "unresolvedConflicts": unresolved_conflicts,
        "securityTips": security_tips,
        "recentActions": recent_actions,
    }
