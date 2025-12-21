"""Declarative base and mixins for CampuSwap models."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


class Base(DeclarativeBase):
    """Declarative base class."""

    metadata = metadata


class PrimaryKeyMixin:
    """Provide a BIGINT primary key."""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)


class TimestampMixin:
    """Provide created/updated timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SyncVersionMixin:
    """Provide sync version column used for optimistic locking."""

    sync_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")


class BaseModel(Base, PrimaryKeyMixin, TimestampMixin, SyncVersionMixin):
    """Base model with common columns."""

    __abstract__ = True
