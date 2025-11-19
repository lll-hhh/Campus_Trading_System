"""
完整的评论路由实现
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_current_user, get_db_session
from apps.core.models import User
from apps.services.business_logic import CommentService

router = APIRouter(prefix="/comments", tags=["评论管理"])


# ==================== Pydantic Models ====================

class CommentCreateRequest(BaseModel):
    """创建评论请求"""
    item_id: int = Field(..., description="商品ID")
    content: str = Field(..., min_length=1, max_length=5000)
    rating: int = Field(default=5, ge=1, le=5)
    parent_comment_id: Optional[int] = Field(None, description="父评论ID(回复)")


class CommentResponse(BaseModel):
    """评论响应"""
    id: int
    item_id: int
    user_id: int
    user_name: str
    user_avatar: Optional[str] = None
    content: str
    rating: int
    parent_comment_id: Optional[int] = None
    reply_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """评论列表响应"""
    comments: List[CommentResponse]
    total: int
    page: int
    page_size: int


# ==================== API路由 ====================

@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    payload: CommentCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """发表评论或回复"""
    comment = CommentService.create_comment(
        session=session,
        item_id=payload.item_id,
        user_id=current_user.id,
        content=payload.content,
        rating=payload.rating,
        parent_comment_id=payload.parent_comment_id
    )
    
    return CommentResponse(
        id=comment.id,
        item_id=comment.item_id,
        user_id=comment.user_id,
        user_name=current_user.username,
        user_avatar=None,
        content=comment.content,
        rating=comment.rating,
        parent_comment_id=comment.parent_comment_id,
        reply_count=0,
        created_at=comment.created_at
    )


@router.get("/items/{item_id}", response_model=CommentListResponse)
async def get_item_comments(
    item_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_db_session)
):
    """获取商品的评论列表"""
    from sqlalchemy import select
    
    comments, total = CommentService.get_item_comments(
        session, item_id, page, page_size
    )
    
    # 转换为响应格式
    comments_data = []
    for comment in comments:
        user = session.get(User, comment.user_id)
        
        # 计算回复数
        reply_count = session.execute(
            select(func.count()).select_from(Comment).where(
                Comment.parent_comment_id == comment.id
            )
        ).scalar() or 0
        
        comments_data.append(CommentResponse(
            id=comment.id,
            item_id=comment.item_id,
            user_id=comment.user_id,
            user_name=user.username if user else "未知用户",
            user_avatar=None,
            content=comment.content,
            rating=comment.rating,
            parent_comment_id=comment.parent_comment_id,
            reply_count=reply_count,
            created_at=comment.created_at
        ))
    
    return CommentListResponse(
        comments=comments_data,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """删除评论"""
    success = CommentService.delete_comment(session, comment_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="评论不存在或无权限")
    return None


@router.get("/my", response_model=CommentListResponse)
async def get_my_comments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """获取我的评论"""
    from apps.core.models import Comment
    from sqlalchemy import select, and_, func, desc
    
    # 查询用户的评论
    query = select(Comment).where(Comment.user_id == current_user.id)
    
    # 总数
    total = session.execute(
        select(func.count()).select_from(Comment).where(Comment.user_id == current_user.id)
    ).scalar() or 0
    
    # 分页
    query = query.order_by(desc(Comment.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    comments = session.execute(query).scalars().all()
    
    # 转换为响应格式
    comments_data = []
    for comment in comments:
        comments_data.append(CommentResponse(
            id=comment.id,
            item_id=comment.item_id,
            user_id=comment.user_id,
            user_name=current_user.username,
            user_avatar=None,
            content=comment.content,
            rating=comment.rating,
            parent_comment_id=comment.parent_comment_id,
            reply_count=0,
            created_at=comment.created_at
        ))
    
    return CommentListResponse(
        comments=comments_data,
        total=total,
        page=page,
        page_size=page_size
    )
