"""Admin endpoints for runtime system settings."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_db_session, require_roles
from apps.core.models import User
from apps.services.system_settings import SystemSettingsService

router = APIRouter(prefix="/admin/settings", tags=["Admin Settings"])


class DatabaseConfigPayload(BaseModel):
    host: str = Field("localhost", description="数据库主机")
    port: int = Field(3306, ge=1, le=65535, description="数据库端口")
    username: str = Field(..., description="数据库用户名")
    password: Optional[str] = Field(None, description="数据库密码")
    database: str = Field(..., description="数据库名称")
    pool_size: int = Field(10, ge=1, le=100, description="连接池大小")


class DatabaseConfigResponse(BaseModel):
    name: str
    label: str
    icon: str
    host: str
    port: int
    username: str
    database: str
    pool_size: int
    has_password: bool
    connected: bool
    status_message: Optional[str]
    last_checked_at: Optional[datetime]
    updated_at: Optional[datetime]


class DatabaseTestPayload(BaseModel):
    config: Optional[DatabaseConfigPayload] = None


class DatabaseTestResult(BaseModel):
    name: str
    connected: bool
    status_message: Optional[str]
    last_checked_at: Optional[datetime]


class SyncConfigPayload(BaseModel):
    mode: str = Field("hybrid", pattern="^(realtime|periodic|hybrid)$")
    interval_minutes: int = Field(15, ge=1, le=1440)
    max_retries: int = Field(3, ge=1, le=10)
    auto_sync_enabled: bool = True


class SyncConfigResponse(SyncConfigPayload):
    updated_at: Optional[datetime] = None


class NotificationConfigPayload(BaseModel):
    smtp_server: str
    smtp_port: int = Field(587, ge=1, le=65535)
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: Optional[EmailStr] = None
    admin_emails: List[EmailStr] = Field(default_factory=list)
    use_tls: bool = True
    notify_conflicts: bool = True
    notify_failures: bool = True
    notify_daily_report: bool = False


class NotificationConfigResponse(NotificationConfigPayload):
    updated_at: Optional[datetime] = None


class NotificationTestPayload(BaseModel):
    recipient: Optional[EmailStr] = None


class NotificationTestResult(BaseModel):
    success: bool
    recipient: Optional[EmailStr] = None
    error: Optional[str] = None


@router.get("/database", response_model=List[DatabaseConfigResponse])
def list_database_configs(
    _: User = Depends(require_roles("admin", "market_admin")),
    session: Session = Depends(get_db_session),
) -> List[DatabaseConfigResponse]:
    service = SystemSettingsService(session)
    return service.list_database_configs()


@router.put("/database/{db_name}", response_model=DatabaseConfigResponse)
def update_database_config(
    db_name: str,
    payload: DatabaseConfigPayload,
    current_user: User = Depends(require_roles("admin", "market_admin")),
    session: Session = Depends(get_db_session),
) -> DatabaseConfigResponse:
    service = SystemSettingsService(session)
    try:
        data = payload.model_dump(exclude_unset=True)
        return service.save_database_config(db_name, data, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/database/{db_name}/test", response_model=DatabaseTestResult)
def test_database_config(
    db_name: str,
    payload: Optional[DatabaseTestPayload] = None,
    _: User = Depends(require_roles("admin", "market_admin")),
    session: Session = Depends(get_db_session),
) -> DatabaseTestResult:
    service = SystemSettingsService(session)
    config_override = payload.config.model_dump(exclude_unset=True) if payload and payload.config else None
    try:
        return service.test_database_connection(db_name, config_override)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/sync", response_model=SyncConfigResponse)
def get_sync_config(
    _: User = Depends(require_roles("admin", "market_admin")),
    session: Session = Depends(get_db_session),
) -> SyncConfigResponse:
    service = SystemSettingsService(session)
    return service.get_sync_config()


@router.put("/sync", response_model=SyncConfigResponse)
def update_sync_config(
    payload: SyncConfigPayload,
    current_user: User = Depends(require_roles("admin", "market_admin")),
    session: Session = Depends(get_db_session),
) -> SyncConfigResponse:
    service = SystemSettingsService(session)
    return service.save_sync_config(payload.model_dump(exclude_unset=True), current_user.id)


@router.get("/notifications", response_model=NotificationConfigResponse)
def get_notification_config(
    _: User = Depends(require_roles("admin", "market_admin")),
    session: Session = Depends(get_db_session),
) -> NotificationConfigResponse:
    service = SystemSettingsService(session)
    return service.get_notification_config()


@router.put("/notifications", response_model=NotificationConfigResponse)
def update_notification_config(
    payload: NotificationConfigPayload,
    current_user: User = Depends(require_roles("admin", "market_admin")),
    session: Session = Depends(get_db_session),
) -> NotificationConfigResponse:
    service = SystemSettingsService(session)
    return service.save_notification_config(payload.model_dump(exclude_unset=True), current_user.id)


@router.post("/notifications/test", response_model=NotificationTestResult)
def test_notification_channel(
    payload: Optional[NotificationTestPayload] = None,
    _: User = Depends(require_roles("admin", "market_admin")),
    session: Session = Depends(get_db_session),
) -> NotificationTestResult:
    service = SystemSettingsService(session)
    recipient = payload.recipient if payload else None
    result = service.test_notification_channel(recipient)
    return NotificationTestResult(**result)
