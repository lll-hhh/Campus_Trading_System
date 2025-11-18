"""Aggregate models for CampuSwap."""
from .ai import AIAction, AIChat, AIInsight, AIModel, FraudPattern
from .base import Base, BaseModel, PrimaryKeyMixin, SyncVersionMixin, TimestampMixin
from .inventory import (
    Category,
    Comment,
    Favorite,
    Follow,
    Item,
    ItemAttachment,
    ItemMedia,
    ItemTag,
    Tag,
)
from .operations import AuditLog, Blacklist, ConfigItem, ModerationTask, Report
from .sync import ConflictRecord, DailyStat, SyncConfig, SyncLog
from .transactions import Delivery, Offer, Payment, Review, Transaction, TransactionLog
from .users import Permission, Role, RolePermission, User, UserProfile, UserRole

__all__ = [
    "AIAction",
    "AIChat",
    "AIInsight",
    "AIModel",
    "AuditLog",
    "Base",
    "BaseModel",
    "Blacklist",
    "Category",
    "Comment",
    "ConfigItem",
    "ConflictRecord",
    "DailyStat",
    "Delivery",
    "Favorite",
    "Follow",
    "FraudPattern",
    "Item",
    "ItemAttachment",
    "ItemMedia",
    "ItemTag",
    "ModerationTask",
    "Offer",
    "Payment",
    "Permission",
    "Report",
    "Review",
    "Role",
    "RolePermission",
    "SyncConfig",
    "SyncLog",
    "Tag",
    "Transaction",
    "TransactionLog",
    "User",
    "UserProfile",
    "UserRole",
]
