"""Inventory and social interaction models."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Category(BaseModel):
    """Item category with hierarchy."""

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))

    parent: Mapped["Category"] = relationship(remote_side="Category.id", backref="children")


class Item(BaseModel):
    """Marketplace listing."""

    __tablename__ = "items"

    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="CNY", nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="draft")
    condition: Mapped[str] = mapped_column(String(32), nullable=False, server_default="good")
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    medias: Mapped[list["ItemMedia"]] = relationship(back_populates="item", cascade="all, delete-orphan")
    attachments: Mapped[list["ItemAttachment"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )


class ItemMedia(BaseModel):
    """Images or videos for an item."""

    __tablename__ = "item_medias"

    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False, index=True)
    media_type: Mapped[str] = mapped_column(String(32), nullable=False, server_default="image")
    url: Mapped[str] = mapped_column(String(512), nullable=False)

    item: Mapped[Item] = relationship(back_populates="medias")


class ItemAttachment(BaseModel):
    """Extra files for an item."""

    __tablename__ = "item_attachments"

    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(64))
    url: Mapped[str] = mapped_column(String(512), nullable=False)

    item: Mapped[Item] = relationship(back_populates="attachments")


class Favorite(BaseModel):
    """User favorites for quick access."""

    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "item_id", name="uq_favorites_user_item"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)


class Follow(BaseModel):
    """Follow relation between users."""

    __tablename__ = "follows"
    __table_args__ = (UniqueConstraint("follower_id", "target_user_id", name="uq_follow_pair"),)

    follower_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)


class Comment(BaseModel):
    """Comments on items."""

    __tablename__ = "comments"

    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parent_comment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comments.id"))

    replies: Mapped[list["Comment"]] = relationship(remote_side="Comment.id")


class Tag(BaseModel):
    """Tag entity for items."""

    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))


class ItemTag(BaseModel):
    """Bridge between items and tags."""

    __tablename__ = "item_tags"
    __table_args__ = (UniqueConstraint("item_id", "tag_id", name="uq_item_tag_pair"),)

    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), nullable=False)
