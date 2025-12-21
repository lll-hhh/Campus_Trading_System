"""
评论路由模块
处理商品评论、评分等功能
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_current_user, get_db_session
from apps.core.models import User

router = APIRouter(prefix="/comments", tags=["评论管理"])


# ==================== Pydantic Models ====================

class CommentCreateRequest(BaseModel):
    """创建评论请求"""
    item_id: int = Field(..., description="商品ID")
    rating: int = Field(..., ge=1, le=5, description="评分(1-5)")
    content: str = Field(..., min_length=5, max_length=1000, description="评论内容")
    images: List[str] = Field(default=[], description="评论图片")


class CommentUpdateRequest(BaseModel):
    """更新评论请求"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    content: Optional[str] = Field(None, min_length=5, max_length=1000)
    images: Optional[List[str]] = None


class CommentResponse(BaseModel):
    """评论响应"""
    id: int
    item_id: int
    user_id: int
    user_name: str
    user_avatar: Optional[str] = None
    rating: int
    content: str
    images: List[str]
    likes: int
    is_liked: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """评论列表响应"""
    comments: List[CommentResponse]
    total: int
    average_rating: float
    rating_distribution: dict
    page: int
    page_size: int


# ==================== API路由 ====================

@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    payload: CommentCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    创建评论
    
    用户可以对购买过的商品进行评价
    """
    # TODO: 验证商品是否存在
    # TODO: 验证用户是否购买过该商品
    # TODO: 验证用户是否已评论
    # TODO: 创建评论记录
    # TODO: 更新商品评分
    
    return CommentResponse(
        id=1,
        item_id=payload.item_id,
        user_id=current_user.id,
        user_name=current_user.username,
        user_avatar=None,
        rating=payload.rating,
        content=payload.content,
        images=payload.images,
        likes=0,
        is_liked=False,
        created_at=datetime.utcnow()
    )


@router.get("/item/{item_id}", response_model=CommentListResponse)
async def get_item_comments(
    item_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    rating: Optional[int] = Query(None, ge=1, le=5, description="按评分筛选"),
    sort_by: str = Query("created_at", description="排序方式: created_at/likes"),
    current_user: Optional[User] = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    获取商品评论列表
    
    支持按评分筛选、按时间或点赞数排序
    """
    # TODO: 查询商品评论
    # TODO: 如果用户已登录，标记用户是否点赞了每条评论
    
    mock_comments = [
        CommentResponse(
            id=i,
            item_id=item_id,
            user_id=100 + i,
            user_name=f"用户{i}",
            user_avatar=f"https://api.dicebear.com/7.x/avataaars/svg?seed=User{i}",
            rating=5 - (i % 5),
            content=f"这是评论内容 {i}，商品质量很好，卖家服务态度也很棒！",
            images=[],
            likes=10 + i * 2,
            is_liked=i % 3 == 0,
            created_at=datetime.utcnow()
        )
        for i in range(1, min(page_size + 1, 11))
    ]
    
    return CommentListResponse(
        comments=mock_comments,
        total=100,
        average_rating=4.5,
        rating_distribution={
            "5": 60,
            "4": 25,
            "3": 10,
            "2": 3,
            "1": 2
        },
        page=page,
        page_size=page_size
    )


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: int,
    session: Session = Depends(get_db_session)
):
    """
    获取评论详情
    """
    # TODO: 查询评论详情
    
    return CommentResponse(
        id=comment_id,
        item_id=1,
        user_id=100,
        user_name="测试用户",
        user_avatar=None,
        rating=5,
        content="这是一条很棒的评论",
        images=[],
        likes=10,
        is_liked=False,
        created_at=datetime.utcnow()
    )


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    payload: CommentUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    更新评论
    
    只能更新自己的评论
    """
    # TODO: 验证评论所有权
    # TODO: 更新评论内容
    
    return CommentResponse(
        id=comment_id,
        item_id=1,
        user_id=current_user.id,
        user_name=current_user.username,
        user_avatar=None,
        rating=payload.rating or 5,
        content=payload.content or "更新后的评论内容",
        images=payload.images or [],
        likes=10,
        is_liked=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    删除评论
    
    只能删除自己的评论
    """
    # TODO: 验证评论所有权
    # TODO: 删除评论
    # TODO: 更新商品评分
    
    return None


@router.post("/{comment_id}/like")
async def toggle_comment_like(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    点赞/取消点赞评论
    """
    # TODO: 切换点赞状态
    
    return {
        "message": "点赞成功",
        "comment_id": comment_id,
        "is_liked": True,
        "likes": 11
    }


@router.get("/user/my-comments", response_model=CommentListResponse)
async def get_my_comments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """
    获取我的评论列表
    """
    # TODO: 查询用户的评论
    
    mock_comments = [
        CommentResponse(
            id=i,
            item_id=i,
            user_id=current_user.id,
            user_name=current_user.username,
            user_avatar=None,
            rating=5,
            content=f"我的评论 {i}",
            images=[],
            likes=5,
            is_liked=False,
            created_at=datetime.utcnow()
        )
        for i in range(1, min(page_size + 1, 6))
    ]
    
    return CommentListResponse(
        comments=mock_comments,
        total=20,
        average_rating=4.8,
        rating_distribution={"5": 15, "4": 4, "3": 1, "2": 0, "1": 0},
        page=page,
        page_size=page_size
    )
