"""
数据库同步API路由 - 同步管理、冲突解决、一致性验证
"""
from typing import Optional, Any, Literal
from datetime import datetime
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text, create_engine

from apps.api_gateway.dependencies import get_db_session, require_roles
from apps.core.models import User
from apps.services.sync_manager import sync_manager


router = APIRouter(prefix="/sync", tags=["数据库同步"])


# ==================== Pydantic Models ====================

class SyncWriteRequest(BaseModel):
    """同步写入请求"""
    table: str = Field(..., description="表名")
    action: str = Field(..., description="操作类型: insert/update/delete")
    data: dict = Field(..., description="数据字典")
    record_id: Optional[int] = Field(None, description="记录ID（用于update/delete）")


class SyncWriteResponse(BaseModel):
    """同步写入响应"""
    status: str
    success_rate: float
    success_dbs: list[str]
    conflicts: list
    timestamp: datetime


class ConsistencyCheckRequest(BaseModel):
    """一致性检查请求"""
    table: str
    record_id: int


class ConsistencyCheckResponse(BaseModel):
    """一致性检查响应"""
    consistent: bool
    data_by_db: dict
    timestamp: datetime


class SyncRepairRequest(BaseModel):
    """同步修复请求"""
    table: str
    record_id: int
    force: bool = False


class SyncRepairResponse(BaseModel):
    """同步修复响应"""
    success: bool
    repaired_dbs: list[str]
    results: dict


class SyncStatsResponse(BaseModel):
    """同步统计响应"""
    success_count: int
    failure_count: int
    conflict_count: int
    success_rate: float


class ConflictRecord(BaseModel):
    """冲突记录"""
    id: int
    table_name: str
    record_id: str
    source: str
    target: str
    resolved: bool
    created_at: datetime
    payload: dict


class ConflictListResponse(BaseModel):
    """冲突列表响应"""
    conflicts: list[ConflictRecord]
    total: int
    page: int
    page_size: int


class SyncLog(BaseModel):
    """同步日志"""
    id: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    stats: dict


class SyncLogListResponse(BaseModel):
    """同步日志列表响应"""
    logs: list[SyncLog]
    total: int
    page: int
    page_size: int


class ConflictResolvePayload(BaseModel):
    """冲突解决请求"""
    strategy: Literal["source", "target", "manual"] = Field(
        default="manual", description="解决策略：采纳来源/source、保留目标/target、手动/manual"
    )


def _parse_json_field(value: Any) -> dict:
    """Safely parse JSON strings into dictionaries."""
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return {}


# ==================== API Endpoints ====================

@router.post("/write", response_model=SyncWriteResponse)
async def sync_write(
    request: SyncWriteRequest,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db_session)
) -> SyncWriteResponse:
    """
    四数据库同步写入
    
    自动将数据写入MySQL、PostgreSQL、MariaDB、SQLite四个数据库
    包含版本控制和冲突检测
    """
    try:
        result = await sync_manager.sync_write(
            table=request.table,
            action=request.action,
            data=request.data,
            record_id=request.record_id,
            user_id=current_user.id
        )
        return SyncWriteResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步写入失败: {str(e)}")


@router.post("/verify-consistency", response_model=ConsistencyCheckResponse)
async def verify_consistency(
    request: ConsistencyCheckRequest,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db_session)
) -> ConsistencyCheckResponse:
    """
    验证数据一致性
    
    检查四个数据库中指定记录的数据是否一致
    """
    try:
        result = await sync_manager.verify_data_consistency(
            table=request.table,
            record_id=request.record_id
        )
        return ConsistencyCheckResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"一致性验证失败: {str(e)}")


@router.post("/repair", response_model=SyncRepairResponse)
async def sync_repair(
    request: SyncRepairRequest,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db_session)
) -> SyncRepairResponse:
    """
    同步修复
    
    从主库（MySQL）读取数据，强制同步到其他数据库
    需要管理员权限
    """
    try:
        result = await sync_manager.sync_repair(
            table=request.table,
            record_id=request.record_id,
            force=request.force
        )
        return SyncRepairResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步修复失败: {str(e)}")


@router.get("/stats", response_model=SyncStatsResponse)
async def get_sync_stats(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db_session)
) -> SyncStatsResponse:
    """
    获取同步统计信息
    """
    stats = sync_manager.get_stats()
    return SyncStatsResponse(**stats)


@router.get("/conflicts", response_model=ConflictListResponse)
def get_conflicts(
    resolved: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db_session)
) -> ConflictListResponse:
    """
    获取冲突记录列表
    
    支持筛选已解决/未解决的冲突
    """
    # 由于表结构与模型不匹配，使用原生SQL
    sql = (
        "SELECT id, table_name, record_id, source_db, target_db, resolved, created_at, "
        "conflict_type, local_data, remote_data, resolution_strategy FROM conflict_records"
    )
    params = {}
    
    if resolved is not None:
        sql += " WHERE resolved = :resolved"
        params["resolved"] = resolved
    
    sql += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
    params["limit"] = page_size
    params["offset"] = (page - 1) * page_size
    
    # 获取总数
    count_sql = "SELECT COUNT(*) FROM conflict_records"
    if resolved is not None:
        count_sql += " WHERE resolved = :resolved"
    
    total_result = db.execute(text(count_sql), params if resolved is not None else {})
    total = total_result.scalar()
    
    # 获取数据
    result = db.execute(text(sql), params)
    rows = result.fetchall()
    
    # 转换为响应格式
    conflicts = []
    for row in rows:
        payload = {
            "type": row[7],
            "local": _parse_json_field(row[8]),
            "remote": _parse_json_field(row[9]),
            "strategy": row[10],
        }
        conflicts.append(
            ConflictRecord(
                id=row[0],
                table_name=row[1],
                record_id=str(row[2]),
                source=row[3],
                target=row[4],
                resolved=bool(row[5]),
                created_at=row[6],
                payload=payload,
            )
        )
    
    return ConflictListResponse(
        conflicts=conflicts,
        total=total,
        page=page,
        page_size=page_size
    )


@router.put("/conflicts/{conflict_id}/resolve")
def resolve_conflict(
    conflict_id: int,
    payload: ConflictResolvePayload,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db_session)
) -> dict:
    """
    标记冲突为已解决并记录策略
    """
    # 检查冲突是否存在
    check_sql = "SELECT id, resolved FROM conflict_records WHERE id = :conflict_id"
    result = db.execute(text(check_sql), {"conflict_id": conflict_id})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="冲突记录不存在")
    
    if row[1]:  # resolved
        raise HTTPException(status_code=400, detail="冲突已解决")
    
    # 更新状态
    update_sql = """
    UPDATE conflict_records 
    SET resolved = 1,
        resolved_by = :user_id,
        resolved_at = NOW(), 
        resolution_strategy = :strategy,
        updated_at = NOW()
    WHERE id = :conflict_id
    """
    db.execute(text(update_sql), {
        "user_id": current_user.id,
        "conflict_id": conflict_id,
        "strategy": payload.strategy
    })
    db.commit()
    
    return {
        "success": True,
        "message": "冲突已标记为已解决",
        "conflict_id": conflict_id,
        "strategy": payload.strategy
    }


@router.get("/logs", response_model=SyncLogListResponse)
async def get_sync_logs(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db_session)
) -> SyncLogListResponse:
    """
    获取同步日志列表
    """
    # 获取总数
    count_sql = "SELECT COUNT(*) FROM sync_logs"
    total_result = db.execute(text(count_sql))
    total = total_result.scalar()
    
    # 分页查询
    sql = """
    SELECT id, config_id, status, started_at, completed_at, stats
    FROM sync_logs
    ORDER BY started_at DESC
    LIMIT :limit OFFSET :offset
    """
    
    result = db.execute(text(sql), {
        "limit": page_size,
        "offset": (page - 1) * page_size
    })
    rows = result.fetchall()
    
    # 转换为响应格式
    logs = [
        SyncLog(
            id=row[0],
            status=row[2],
            started_at=row[3],
            completed_at=row[4],
            stats=_parse_json_field(row[5])
        )
        for row in rows
    ]
    
    return SyncLogListResponse(
        logs=logs,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/databases/status")
async def get_database_status(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db_session)
) -> dict:
    """
    获取四个数据库的状态信息
    """
    from apps.core.config import Settings
    
    settings = Settings()
    
    databases = []
    
    # MySQL
    mysql_status = await check_database_health(
        "MySQL",
        settings.mysql_dsn,
        "mysql",
        "MySQL 8.0"
    )
    databases.append(mysql_status)
    
    # MariaDB
    mariadb_status = await check_database_health(
        "MariaDB", 
        settings.mariadb_dsn,
        "mariadb",
        "MariaDB 10.6"
    )
    databases.append(mariadb_status)
    
    # PostgreSQL
    postgres_status = await check_database_health(
        "PostgreSQL",
        settings.postgres_dsn,
        "postgres", 
        "PostgreSQL 14"
    )
    databases.append(postgres_status)
    
    # SQLite - 直接检查文件
    sqlite_path = "/app/data/campuswap.db"
    import os
    sqlite_status = {
        "name": "sqlite",
        "label": "SQLite",
        "type": "SQLite 3",
        "host": sqlite_path,
        "status": "healthy" if os.path.exists(sqlite_path) else "error",
        "sync_progress": 100,
        "latency": 1,
        "last_sync": datetime.utcnow()
    }
    databases.append(sqlite_status)
    
    return {"databases": databases}


async def check_database_health(name: str, dsn: str, db_type: str, version: str) -> dict:
    """检查单个数据库健康状态"""
    import time
    
    start_time = time.time()
    status = "healthy"
    latency = 0
    
    try:
        engine = create_engine(dsn, pool_pre_ping=True)
        with engine.connect() as conn:
            # 执行简单查询
            if db_type == "mysql":
                conn.execute(text("SELECT 1"))
            elif db_type == "postgres":
                conn.execute(text("SELECT 1"))
            elif db_type == "mariadb":
                conn.execute(text("SELECT 1"))
            
            latency = int((time.time() - start_time) * 1000)
            
            # 检查同步进度（简化版）
            sync_progress = 100  # 暂时设为100
            
    except Exception:
        status = "error"
        latency = 9999
        sync_progress = 0
    
    return {
        "name": db_type,
        "label": f"{name} ({'主库' if db_type == 'mysql' else '从库'})",
        "type": version,
        "host": dsn.split('@')[-1] if '@' in dsn else f"{db_type}:3306",
        "status": status,
        "sync_progress": sync_progress,
        "latency": latency,
        "last_sync": datetime.utcnow()
    }
