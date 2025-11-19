"""
补充模型：购物车、搜索、会话、刷新令牌
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from apps.core.models.base import Base, TimestampMixin


# ==================== 购物车模型 ====================

class CartItem(Base, TimestampMixin):
    """购物车表"""
    __tablename__ = "cart_items"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    item_id = Column(BigInteger, nullable=False, comment="商品ID")
    quantity = Column(Integer, nullable=False, default=1, comment="数量")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'item_id', name='unique_user_item'),
        Index('idx_user_id', 'user_id'),
        Index('idx_item_id', 'item_id'),
        Index('idx_created', 'created_at'),
    )


# ==================== 搜索模型 ====================

class SearchHistory(Base):
    """搜索历史表"""
    __tablename__ = "search_history"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    keyword = Column(String(200), nullable=False, comment="搜索关键词")
    result_count = Column(Integer, default=0, comment="搜索结果数量")
    search_type = Column(
        Enum('keyword', 'category', 'advanced', name='search_type_enum'),
        default='keyword',
        comment="搜索类型"
    )
    filters = Column(JSON, comment="搜索过滤条件(JSON)")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_keyword', 'keyword'),
        Index('idx_created', 'created_at'),
        Index('idx_user_created', 'user_id', 'created_at'),
    )


class SearchTrending(Base):
    """热门搜索统计表"""
    __tablename__ = "search_trending"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    keyword = Column(String(200), nullable=False, comment="搜索关键词")
    search_count = Column(Integer, default=1, comment="搜索次数")
    last_searched_at = Column(DateTime, default=datetime.utcnow, comment="最后搜索时间")
    date = Column(Date, nullable=False, comment="统计日期")
    
    __table_args__ = (
        UniqueConstraint('keyword', 'date', name='unique_keyword_date'),
        Index('idx_search_count', 'search_count'),
        Index('idx_date', 'date'),
        Index('idx_last_searched', 'last_searched_at'),
    )


# ==================== 会话模型 ====================

class Conversation(Base, TimestampMixin):
    """会话表（消息聊天）"""
    __tablename__ = "conversations"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user1_id = Column(BigInteger, nullable=False, comment="用户1 ID")
    user2_id = Column(BigInteger, nullable=False, comment="用户2 ID")
    item_id = Column(BigInteger, comment="关联商品ID（可选）")
    
    # 最后消息信息
    last_message_id = Column(BigInteger, comment="最后一条消息ID")
    last_message_content = Column(Text, comment="最后消息内容")
    last_message_at = Column(DateTime, comment="最后消息时间")
    
    # 未读计数
    user1_unread_count = Column(Integer, default=0, comment="用户1未读消息数")
    user2_unread_count = Column(Integer, default=0, comment="用户2未读消息数")
    
    # 删除标记
    user1_deleted = Column(Boolean, default=False, comment="用户1是否删除")
    user2_deleted = Column(Boolean, default=False, comment="用户2是否删除")
    
    __table_args__ = (
        UniqueConstraint('user1_id', 'user2_id', name='unique_users'),
        Index('idx_user1', 'user1_id', 'user1_deleted'),
        Index('idx_user2', 'user2_id', 'user2_deleted'),
        Index('idx_item', 'item_id'),
        Index('idx_updated', 'updated_at'),
    )


# ==================== 刷新令牌模型 ====================

class RefreshToken(Base):
    """刷新令牌表（用于JWT刷新）"""
    __tablename__ = "refresh_tokens"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    token = Column(String(500), unique=True, nullable=False, comment="刷新令牌")
    access_token = Column(String(500), comment="关联的访问令牌")
    
    # Token有效期
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    
    # 设备和IP信息
    device_info = Column(String(500), comment="设备信息")
    ip_address = Column(String(50), comment="IP地址")
    user_agent = Column(Text, comment="用户代理")
    
    # 状态
    is_revoked = Column(Boolean, default=False, comment="是否已撤销")
    revoked_at = Column(DateTime, comment="撤销时间")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_expires', 'expires_at'),
        Index('idx_revoked', 'is_revoked'),
    )
