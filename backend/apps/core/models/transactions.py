"""Transaction and fulfillment related models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Offer(BaseModel):
    """Buyer offer for an item."""

    __tablename__ = "offers"

    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="pending")
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Transaction(BaseModel):
    """Confirmed transaction between buyer and seller."""

    __tablename__ = "transactions"

    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"), nullable=False, unique=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="initiated")
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, server_default="CNY")

    offer: Mapped[Offer] = relationship()


class TransactionLog(BaseModel):
    """State transitions for transactions."""

    __tablename__ = "transaction_logs"

    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    old_status: Mapped[Optional[str]] = mapped_column(String(32))
    new_status: Mapped[Optional[str]] = mapped_column(String(32))
    extra_data: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")


class Payment(BaseModel):
    """Payment records."""

    __tablename__ = "payments"

    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    reference: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="pending")
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Delivery(BaseModel):
    """Delivery tracking entries."""

    __tablename__ = "deliveries"

    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    carrier: Mapped[Optional[str]] = mapped_column(String(64))
    tracking_number: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="preparing")
    estimated_arrival: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Review(BaseModel):
    """Peer review after transaction."""

    __tablename__ = "reviews"

    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), nullable=False, unique=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    comment: Mapped[Optional[str]] = mapped_column(Text)
