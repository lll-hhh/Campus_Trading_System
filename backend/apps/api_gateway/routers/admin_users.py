"""Admin-facing user & role management APIs."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_db_session, require_roles
from apps.core.models import Role
from apps.services.admin_users import AdminUserService

router = APIRouter(
    prefix="/admin",
    tags=["Admin Users"],
    dependencies=[Depends(require_roles("admin", "market_admin"))],
)


class UserCreatePayload(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    is_active: bool = True
    is_verified: bool = False
    role_ids: List[int] = Field(default_factory=list)


class UserUpdatePayload(BaseModel):
    username: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role_ids: Optional[List[int]] = None


class RoleCreatePayload(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    permission_ids: List[int] = Field(default_factory=list)


class RoleUpdatePayload(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    permission_ids: Optional[List[int]] = None


class RolePermissionPayload(BaseModel):
    permission_ids: List[int] = Field(default_factory=list)


def _service(session: Session) -> AdminUserService:
    return AdminUserService(session)


@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(None, description="用户名、邮箱或学号模糊搜索"),
    session: Session = Depends(get_db_session),
):
    service = _service(session)
    return service.list_users(page=page, page_size=page_size, search=search)


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreatePayload, session: Session = Depends(get_db_session)):
    service = _service(session)
    try:
        result = service.create_user(**payload.model_dump())
        session.commit()
        return result
    except ValueError as exc:  # duplicate or missing roles
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/users/{user_id}")
def update_user(user_id: int, payload: UserUpdatePayload, session: Session = Depends(get_db_session)):
    service = _service(session)
    user = service.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    try:
        result = service.update_user(user=user, **payload.model_dump(exclude_unset=True))
        session.commit()
        return result
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, session: Session = Depends(get_db_session)):
    service = _service(session)
    user = service.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    service.delete_user(user=user)
    session.commit()
    return {"deleted": True}


@router.get("/roles")
def list_roles(session: Session = Depends(get_db_session)):
    service = _service(session)
    return service.list_roles()


@router.post("/roles", status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleCreatePayload, session: Session = Depends(get_db_session)):
    service = _service(session)
    try:
        result = service.create_role(**payload.model_dump())
        session.commit()
        return result
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/roles/{role_id}")
def update_role(role_id: int, payload: RoleUpdatePayload, session: Session = Depends(get_db_session)):
    service = _service(session)
    role = session.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    try:
        result = service.update_role(role=role, **payload.model_dump(exclude_unset=True))
        session.commit()
        return result
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, session: Session = Depends(get_db_session)):
    service = _service(session)
    role = session.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    service.delete_role(role=role)
    session.commit()
    return {"deleted": True}


@router.put("/roles/{role_id}/permissions")
def update_role_permissions(role_id: int, payload: RolePermissionPayload, session: Session = Depends(get_db_session)):
    service = _service(session)
    role = session.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    try:
        result = service.update_role_permissions(role=role, **payload.model_dump())
        session.commit()
        return result
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/permissions")
def list_permissions(session: Session = Depends(get_db_session)):
    service = _service(session)
    return service.list_permissions()
