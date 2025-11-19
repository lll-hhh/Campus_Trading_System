"""
数据库同步API路由 - 同步管理、冲突解决、一致性验证
"""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_current_user, get_db_session
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


# ==================== API Endpoints ====================

@router.post("/write", response_model=SyncWriteResponse)
async def sync_write(
    request: SyncWriteRequest,
    current_user: dict = Depends(get_current_user),
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
            user_id=current_user["id"]
        )
        return SyncWriteResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步写入失败: {str(e)}")


@router.post("/verify-consistency", response_model=ConsistencyCheckResponse)
async def verify_consistency(
    request: ConsistencyCheckRequest,
    current_user: dict = Depends(get_current_user),
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> SyncRepairResponse:
    """
    同步修复
    
    从主库（MySQL）读取数据，强制同步到其他数据库
    需要管理员权限
    """
    # 检查管理员权限
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> SyncStatsResponse:
    """
    获取同步统计信息
    """
    stats = sync_manager.get_stats()
    return SyncStatsResponse(**stats)


@router.get("/conflicts", response_model=ConflictListResponse)
async def get_conflicts(
    resolved: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> ConflictListResponse:
    """
    获取冲突记录列表
    
    支持筛选已解决/未解决的冲突
    """
    # TODO: 从数据库查询冲突记录
    # 当前返回模拟数据
    
    mock_conflicts = [
        ConflictRecord(
            id=1,
            table_name="items",
            record_id="12345",
            source="mysql",
            target="postgres,mariadb",
            resolved=False,
            created_at=datetime.utcnow(),
            payload={"type": "version_conflict", "version": 5}
        )
    ]
    
    # 筛选
    if resolved is not None:
        mock_conflicts = [c for c in mock_conflicts if c.resolved == resolved]
    
    # 分页
    total = len(mock_conflicts)
    start = (page - 1) * page_size
    end = start + page_size
    conflicts = mock_conflicts[start:end]
    
    return ConflictListResponse(
        conflicts=conflicts,
        total=total,
        page=page,
        page_size=page_size
    )


@router.put("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> dict:
    """
    标记冲突为已解决
    """
    # TODO: 更新数据库中的冲突记录
    
    return {
        "success": True,
        "message": "冲突已标记为已解决",
        "conflict_id": conflict_id
    }


@router.get("/logs", response_model=SyncLogListResponse)
async def get_sync_logs(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> SyncLogListResponse:
    """
    获取同步日志列表
    """
    # TODO: 从数据库查询同步日志
    # 当前返回模拟数据
    
    mock_logs = [
        SyncLog(
            id=1,
            status="completed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            stats={
                "table": "items",
                "action": "update",
                "success_count": 3,
                "total_count": 4
            }
        )
    ]
    
    # 分页
    total = len(mock_logs)
    start = (page - 1) * page_size
    end = start + page_size
    logs = mock_logs[start:end]
    
    return SyncLogListResponse(
        logs=logs,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/databases/status")
async def get_database_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> dict:
    """
    获取四个数据库的状态信息
    """
    # TODO: 实现真实的数据库状态检测
    # 当前返回模拟数据
    
    return {
        "databases": [
            {
                "name": "mysql",
                "label": "MySQL (主库)",
                "type": "MySQL 8.0",
                "host": "localhost:3306",
                "status": "healthy",
                "sync_progress": 100,
                "latency": 5,
                "last_sync": datetime.utcnow()
            },
            {
                "name": "postgres",
                "label": "PostgreSQL",
                "type": "PostgreSQL 15",
                "host": "localhost:5432",
                "status": "healthy",
                "sync_progress": 98,
                "latency": 8,
                "last_sync": datetime.utcnow()
            },
            {
                "name": "mariadb",
                "label": "MariaDB",
                "type": "MariaDB 10.11",
                "host": "localhost:3307",
                "status": "warning",
                "sync_progress": 95,
                "latency": 12,
                "last_sync": datetime.utcnow()
            },
            {
                "name": "sqlite",
                "label": "SQLite",
                "type": "SQLite 3",
                "host": "campus_swap.db",
                "status": "healthy",
                "sync_progress": 100,
                "latency": 2,
                "last_sync": datetime.utcnow()
            }
        ]
    }
