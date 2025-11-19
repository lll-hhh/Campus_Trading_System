"""
消息/聊天路由模块
处理用户间的消息发送、接收、会话管理等功能
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_current_user, get_db_session
from apps.core.models import User

router = APIRouter(prefix="/messages", tags=["消息管理"])


# ==================== Pydantic Models ====================

class MessageSendRequest(BaseModel):
    """发送消息请求"""
    receiver_id: int = Field(..., description="接收者ID")
    content: str = Field(..., min_length=1, max_length=5000, description="消息内容")
    message_type: str = Field(default="text", description="消息类型: text/image/file")
    item_id: Optional[int] = Field(None, description="关联商品ID")


class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    conversation_id: int
    sender_id: int
    sender_name: str
    sender_avatar: Optional[str] = None
    receiver_id: int
    receiver_name: str
    receiver_avatar: Optional[str] = None
    content: str
    message_type: str
    item_id: Optional[int] = None
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """会话响应"""
    id: int
    other_user_id: int
    other_user_name: str
    other_user_avatar: Optional[str] = None
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """消息列表响应"""
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int


class ConversationListResponse(BaseModel):
    """会话列表响应"""
    conversations: List[ConversationResponse]
    total: int
    total_unread: int


# ==================== API路由 ====================

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    payload: MessageSendRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    发送消息
    
    可以关联商品ID，方便买卖双方沟通
    """
    # TODO: 验证接收者是否存在
    # TODO: 创建或获取会话
    # TODO: 创建消息记录
    # TODO: 发送实时通知（WebSocket）
    
    return MessageResponse(
        id=1,
        conversation_id=1,
        sender_id=current_user.id,
        sender_name=current_user.username,
        sender_avatar=None,
        receiver_id=payload.receiver_id,
        receiver_name="接收者",
        receiver_avatar=None,
        content=payload.content,
        message_type=payload.message_type,
        item_id=payload.item_id,
        is_read=False,
        created_at=datetime.utcnow()
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    获取会话列表
    
    按最后消息时间排序
    """
    # TODO: 查询用户的所有会话
    
    mock_conversations = [
        ConversationResponse(
            id=i,
            other_user_id=100 + i,
            other_user_name=f"用户{i}",
            other_user_avatar=f"https://api.dicebear.com/7.x/avataaars/svg?seed=User{i}",
            last_message=f"这是最后一条消息内容 {i}",
            last_message_time=datetime.utcnow(),
            unread_count=i * 2,
            created_at=datetime.utcnow()
        )
        for i in range(1, 6)
    ]
    
    total_unread = sum(conv.unread_count for conv in mock_conversations)
    
    return ConversationListResponse(
        conversations=mock_conversations,
        total=len(mock_conversations),
        total_unread=total_unread
    )


@router.get("/conversations/{conversation_id}", response_model=MessageListResponse)
async def get_conversation_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    获取会话消息列表
    
    按时间倒序返回，支持分页加载历史消息
    """
    # TODO: 验证会话权限
    # TODO: 查询消息列表
    # TODO: 标记消息为已读
    
    mock_messages = [
        MessageResponse(
            id=i,
            conversation_id=conversation_id,
            sender_id=current_user.id if i % 2 == 0 else 100,
            sender_name=current_user.username if i % 2 == 0 else "对方用户",
            sender_avatar=None,
            receiver_id=100 if i % 2 == 0 else current_user.id,
            receiver_name="对方用户" if i % 2 == 0 else current_user.username,
            receiver_avatar=None,
            content=f"这是消息内容 {i}",
            message_type="text",
            is_read=i % 2 == 1,
            created_at=datetime.utcnow()
        )
        for i in range(1, min(page_size + 1, 21))
    ]
    
    return MessageListResponse(
        messages=mock_messages,
        total=100,
        page=page,
        page_size=page_size
    )


@router.put("/{message_id}/read")
async def mark_message_read(
    message_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    标记消息为已读
    """
    # TODO: 验证消息接收者
    # TODO: 更新已读状态
    
    return {"message": "消息已标记为已读", "message_id": message_id}


@router.put("/conversations/{conversation_id}/read")
async def mark_conversation_read(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    标记会话所有消息为已读
    """
    # TODO: 批量更新会话消息为已读
    
    return {"message": "会话消息已全部标记为已读", "conversation_id": conversation_id}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    删除会话
    
    注意：只是隐藏会话，不会删除消息记录
    """
    # TODO: 软删除会话
    
    return {"message": "会话已删除", "conversation_id": conversation_id}


@router.get("/unread/count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    获取未读消息总数
    
    用于顶部导航栏的徽章显示
    """
    # TODO: 统计未读消息数
    
    return {
        "total_unread": 5,
        "conversations_with_unread": 3
    }


@router.get("/search")
async def search_messages(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    搜索消息
    
    支持按内容、联系人名称搜索
    """
    # TODO: 全文搜索消息
    
    return {
        "results": [],
        "total": 0,
        "keyword": keyword
    }
