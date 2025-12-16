"""User domain entities and roles."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .inventory import Item


class User(BaseModel):
    """Registered platform user."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    student_id: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True, index=True)
    
    hashed_password: Mapped[str] = mapped_column("password_hash", String(255), nullable=False)
    
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    real_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    
    credit_score: Mapped[int] = mapped_column(Integer, default=100, index=True)
    seller_rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("5.00"))
    buyer_rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("5.00"))
    total_sales: Mapped[int] = mapped_column(Integer, default=0)
    total_purchases: Mapped[int] = mapped_column(Integer, default=0)
    
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ✅ 关系
    profile: Mapped[Optional["UserProfile"]] = relationship(back_populates="user", uselist=False)
    preferences: Mapped[Optional["UserPreference"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    roles: Mapped[List["Role"]] = relationship(
        secondary="user_roles",
        back_populates="users",
        lazy="selectin"
    )
    
    # ✅ 新增：用户发布的商品
    items: Mapped[List["Item"]] = relationship(
        back_populates="seller",
        lazy="selectin",
        foreign_keys="Item.seller_id"
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


class UserPreference(BaseModel):
    """Per-user privacy and notification toggles."""

    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    show_email: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    show_phone: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_follow: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_message: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_notification: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    message_notification: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    transaction_notification: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    comment_notification: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    system_notification: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped[User] = relationship(back_populates="preferences")


class Role(BaseModel):
    """User role for RBAC."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    
    users: Mapped[List[User]] = relationship(
        secondary="user_roles",
        back_populates="roles",
        lazy="selectin"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin"
    )


class Permission(BaseModel):
    """Granular permission."""

    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    
    roles: Mapped[List[Role]] = relationship(
        secondary="role_permissions",
        back_populates="permissions",
        lazy="selectin"
    )


class UserRole(BaseModel):
    """Association table for users and roles."""

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)


class RolePermission(BaseModel):
    """Association table for roles and permissions."""

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), nullable=False)