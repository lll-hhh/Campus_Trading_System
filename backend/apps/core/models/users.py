"""User and permission related models."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class User(BaseModel):
    """Registered platform user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="active")
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False)
    roles: Mapped[List["Role"]] = relationship(
        secondary="user_roles", back_populates="users", lazy="selectin"
    )


class UserProfile(BaseModel):
    """Extended profile info for a user."""

    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    campus: Mapped[Optional[str]] = mapped_column(String(120))
    bio: Mapped[Optional[str]] = mapped_column(String(500))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512))

    user: Mapped[User] = relationship(back_populates="profile")


class Role(BaseModel):
    """Role entity for RBAC."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    permissions: Mapped[List["Permission"]] = relationship(
        secondary="role_permissions", back_populates="roles", lazy="selectin"
    )
    users: Mapped[List[User]] = relationship(
        secondary="user_roles", back_populates="roles", lazy="selectin"
    )


class Permission(BaseModel):
    """Fine-grained permission entry."""

    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    roles: Mapped[List[Role]] = relationship(
        secondary="role_permissions", back_populates="permissions", lazy="selectin"
    )


class RolePermission(BaseModel):
    """Bridge between roles and permissions."""

    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_pair"),)

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), nullable=False)

    role: Mapped[Role] = relationship(back_populates="permissions")
    permission: Mapped[Permission] = relationship(back_populates="roles")


class UserRole(BaseModel):
    """Bridge between users and roles."""

    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_roles_pair"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)

    user: Mapped[User] = relationship(back_populates="roles")
    role: Mapped[Role] = relationship(back_populates="users")
