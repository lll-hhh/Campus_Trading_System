"""AI related persistence models."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class AIChat(BaseModel):
    """Chat interactions with AI assistant."""

    __tablename__ = "ai_chats"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, server_default="user")
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")


class AIAction(BaseModel):
    """Record of automated AI decisions."""

    __tablename__ = "ai_actions"

    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    result: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="pending")


class AIModel(BaseModel):
    """Registered AI models or API endpoints."""

    __tablename__ = "ai_models"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)


class AIInsight(BaseModel):
    """Insights produced for listings or risks."""

    __tablename__ = "ai_insights"

    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    insight_type: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)


class FraudPattern(BaseModel):
    """Rule definition for risk management."""

    __tablename__ = "fraud_patterns"

    rule_name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    rule_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
