"""Inventory and listing related domain entities."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .users import User


class Category(BaseModel):
    """Product category."""

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    icon: Mapped[Optional[str]] = mapped_column(String(100))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    items: Mapped[list["Item"]] = relationship(back_populates="category")


class Item(BaseModel):
    """Marketplace listing."""

    __tablename__ = "items"

    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), nullable=True)
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    original_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # 使用数据库实际存在的字段名
    condition_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="二手")
    
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_info: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="available", index=True)
    
    is_negotiable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_shipped: Mapped[bool] = mapped_column(Boolean, default=False)
    
    view_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    favorite_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    inquiry_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # ✅ 属性方法：提供 currency 和 condition 的兼容访问
    @property
    def currency(self) -> str:
        """兼容旧代码：返回默认货币"""
        return "CNY"
    
    @property
    def condition(self) -> str:
        """兼容旧代码：映射 condition_type 到 condition"""
        mapping = {
            "全新": "new",
            "99新": "like_new",
            "95新": "very_good",
            "9成新": "good",
            "二手": "used",
        }
        return mapping.get(self.condition_type or "二手", "used")

    # ✅ 关系定义
    seller: Mapped["User"] = relationship(
        back_populates="items",
        lazy="selectin",
        foreign_keys=[seller_id]
    )
    category: Mapped[Optional["Category"]] = relationship(
        back_populates="items",
        lazy="selectin"
    )
    medias: Mapped[list["ItemMedia"]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class ItemMedia(BaseModel):
    """Attachments (images/videos) for an item."""

    __tablename__ = "item_images"

    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False)

    item: Mapped["Item"] = relationship(back_populates="medias")
    
    @property
    def url(self) -> str:
        """兼容旧代码"""
        return self.image_url
    
    @property
    def media_type(self) -> str:
        """兼容旧代码"""
        return "image"


class Favorite(BaseModel):
    """User favorites."""

    __tablename__ = "favorites"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)


class Comment(BaseModel):
    """Item comments/reviews."""

    __tablename__ = "comments"

    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comments.id"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


# 保留其他模型类
class Follow(BaseModel):
    """User follows."""
    __tablename__ = "user_follows"
    
    follower_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    following_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)


class Tag(BaseModel):
    """Item tags."""
    __tablename__ = "tags"
    
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)


class ItemTag(BaseModel):
    """Item-Tag association."""
    __tablename__ = "item_tags"
    
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), nullable=False)


class ItemAttachment(BaseModel):
    """Item attachments (alias for ItemMedia)."""
    __tablename__ = "item_attachments"
    
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
