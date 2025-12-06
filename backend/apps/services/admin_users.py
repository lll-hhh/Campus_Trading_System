"""Administrative user and role management services."""
from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from apps.core.models import Permission, Role, RolePermission, User
from apps.core.security import get_password_hash


class AdminUserService:
    """Encapsulates RBAC management helpers for admin APIs."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ---------------------------------------------------------------------
    # User helpers
    # ---------------------------------------------------------------------
    def list_users(self, *, page: int, page_size: int, search: Optional[str] = None) -> Dict[str, object]:
        filters = []
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    User.username.ilike(pattern),
                    User.email.ilike(pattern),
                    User.student_id.ilike(pattern),
                )
            )

        base_query = select(User).options(selectinload(User.roles))
        count_query = select(func.count()).select_from(User)
        if filters:
            base_query = base_query.where(*filters)
            count_query = count_query.where(*filters)

        total = self.session.execute(count_query).scalar_one()

        rows = (
            self.session.execute(
                base_query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
            )
            .scalars()
            .all()
        )

        return {
            "items": [self._serialize_user(user) for user in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_user(self, user_id: int) -> Optional[User]:
        return self.session.get(User, user_id)

    def ensure_unique_user(self, *, username: str, email: str, exclude_id: Optional[int] = None) -> None:
        query = select(User).where(or_(User.username == username, User.email == email))
        if exclude_id is not None:
            query = query.where(User.id != exclude_id)
        existing = self.session.execute(query.limit(1)).scalar_one_or_none()
        if existing:
            raise ValueError("用户名或邮箱已存在")

    def create_user(
        self,
        *,
        username: str,
        email: str,
        password: str,
        is_active: bool,
        is_verified: bool,
        role_ids: Optional[List[int]] = None,
    ) -> Dict[str, object]:
        self.ensure_unique_user(username=username, email=email)
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            is_active=is_active,
            is_verified=is_verified,
        )
        if role_ids:
            user.roles = self._fetch_roles(role_ids)
        self.session.add(user)
        self.session.flush()
        return self._serialize_user(user)

    def update_user(
        self,
        *,
        user: User,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        role_ids: Optional[List[int]] = None,
    ) -> Dict[str, object]:
        if username and username != user.username:
            self.ensure_unique_user(username=username, email=user.email, exclude_id=user.id)
            user.username = username
        if email and email != user.email:
            self.ensure_unique_user(username=user.username, email=email, exclude_id=user.id)
            user.email = email
        if password:
            user.hashed_password = get_password_hash(password)
        if is_active is not None:
            user.is_active = is_active
        if is_verified is not None:
            user.is_verified = is_verified
        if role_ids is not None:
            user.roles = self._fetch_roles(role_ids)
        self.session.flush()
        return self._serialize_user(user)

    def delete_user(self, *, user: User) -> None:
        self.session.delete(user)

    # ------------------------------------------------------------------
    # Roles & permissions
    # ------------------------------------------------------------------
    def list_roles(self) -> List[Dict[str, object]]:
        rows = (
            self.session.execute(select(Role).options(selectinload(Role.permissions)).order_by(Role.id.asc()))
            .scalars()
            .all()
        )
        return [self._serialize_role(role) for role in rows]

    def create_role(self, *, name: str, description: Optional[str], permission_ids: Optional[List[int]]) -> Dict[str, object]:
        if self.session.execute(select(Role).where(Role.name == name).limit(1)).scalar_one_or_none():
            raise ValueError("角色名称已存在")
        role = Role(name=name, description=description)
        if permission_ids:
            role.permissions = self._fetch_permissions(permission_ids)
        self.session.add(role)
        self.session.flush()
        return self._serialize_role(role)

    def update_role(
        self,
        *,
        role: Role,
        name: Optional[str] = None,
        description: Optional[str] = None,
        permission_ids: Optional[List[int]] = None,
    ) -> Dict[str, object]:
        if name and name != role.name:
            if self.session.execute(select(Role).where(Role.name == name, Role.id != role.id)).scalar_one_or_none():
                raise ValueError("角色名称已存在")
            role.name = name
        if description is not None:
            role.description = description
        if permission_ids is not None:
            role.permissions = self._fetch_permissions(permission_ids)
        self.session.flush()
        return self._serialize_role(role)

    def delete_role(self, *, role: Role) -> None:
        self.session.delete(role)

    def update_role_permissions(self, *, role: Role, permission_ids: List[int]) -> Dict[str, object]:
        role.permissions = self._fetch_permissions(permission_ids)
        self.session.flush()
        return self._serialize_role(role)

    def list_permissions(self) -> List[Dict[str, object]]:
        rows = self.session.execute(
            select(
                Permission,
                func.count(RolePermission.id).label("role_count"),
            )
                .outerjoin(RolePermission, RolePermission.permission_id == Permission.id)
                .group_by(Permission.id)
                .order_by(Permission.name.asc())
        )
        return [
            {
                **self._serialize_permission(permission),
                "role_count": role_count or 0,
            }
            for permission, role_count in rows.all()
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _fetch_roles(self, role_ids: List[int]) -> List[Role]:
        if not role_ids:
            return []
        rows = self.session.execute(select(Role).where(Role.id.in_(role_ids))).scalars().all()
        if len(rows) != len(set(role_ids)):
            raise ValueError("部分角色不存在")
        return rows

    def _fetch_permissions(self, permission_ids: List[int]) -> List[Permission]:
        if not permission_ids:
            return []
        rows = self.session.execute(select(Permission).where(Permission.id.in_(permission_ids))).scalars().all()
        if len(rows) != len(set(permission_ids)):
            raise ValueError("部分权限不存在")
        return rows

    @staticmethod
    def _serialize_user(user: User) -> Dict[str, object]:
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "roles": [role.name for role in user.roles],
            "role_ids": [role.id for role in user.roles],
        }

    @staticmethod
    def _serialize_role(role: Role) -> Dict[str, object]:
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions": [
                {
                    "id": permission.id,
                    "name": permission.name,
                    "resource": permission.resource,
                    "action": permission.action,
                }
                for permission in role.permissions
            ],
            "permission_ids": [permission.id for permission in role.permissions],
        }

    @staticmethod
    def _serialize_permission(permission: Permission) -> Dict[str, object]:
        return {
            "id": permission.id,
            "name": permission.name,
            "resource": permission.resource,
            "action": permission.action,
            "description": permission.description,
        }
