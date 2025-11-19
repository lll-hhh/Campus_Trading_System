"""Authentication routes with role-aware JWT tokens."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from apps.api_gateway.dependencies import get_current_user, get_db_session
from apps.core.models import User
from apps.core.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenResponse(BaseModel):
    """Token plus user info response."""

    access_token: str
    token_type: str = "bearer"
    user_id: int
    roles: list[str]
    display_name: str | None = None


class LoginRequest(BaseModel):
    """Login payload placeholder."""

    email: EmailStr
    password: str
    remember: bool = Field(default=False, description="记住我")


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=20, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    student_id: str = Field(..., pattern=r"^[0-9]{8,12}$", description="学号")
    password: str = Field(..., min_length=6, description="密码")
    confirm_password: str = Field(..., description="确认密码")


class RefreshTokenRequest(BaseModel):
    """刷新token请求"""
    refresh_token: str


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_db_session)) -> TokenResponse:
    """Issue an access token after validating credentials against the DB."""

    user = session.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    roles = [role.name for role in user.roles]
    
    # 如果选择"记住我"，延长token有效期
    expires_delta = timedelta(days=7) if payload.remember else timedelta(minutes=60)
    
    token = create_access_token(
        subject=user.email,
        roles=roles,
        user_id=user.id,
        expires_delta=expires_delta,
    )
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        roles=roles,
        display_name=user.profile.display_name if user.profile else None,
    )


@router.get("/me", response_model=TokenResponse)
def read_me(user: User = Depends(get_current_user)) -> TokenResponse:
    """Return current user profile info and a refreshed token."""

    roles = [role.name for role in user.roles]
    token = create_access_token(user.email, roles=roles, user_id=user.id)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        roles=roles,
        display_name=user.profile.display_name if user.profile else None,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    session: Session = Depends(get_db_session)
) -> TokenResponse:
    """
    用户注册
    
    创建新用户账号并返回访问token
    """
    # 验证两次密码是否一致
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="两次输入的密码不一致"
        )
    
    # 检查用户名是否已存在
    existing_user = session.execute(
        select(User).where(User.username == payload.username)
    ).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被使用"
        )
    
    # 检查邮箱是否已存在
    existing_email = session.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 检查学号是否已存在 (假设User模型有student_id字段)
    # existing_student = session.execute(
    #     select(User).where(User.student_id == payload.student_id)
    # ).scalar_one_or_none()
    # if existing_student:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="学号已被注册"
    #     )
    
    # 创建新用户
    from apps.core.security import get_password_hash
    new_user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        created_at=datetime.utcnow()
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    # 返回token
    token = create_access_token(
        subject=new_user.email,
        roles=[],
        user_id=new_user.id,
        expires_delta=timedelta(minutes=60)
    )
    
    return TokenResponse(
        access_token=token,
        user_id=new_user.id,
        roles=[],
        display_name=new_user.username
    )


@router.post("/logout")
def logout(user: User = Depends(get_current_user)):
    """
    用户登出
    
    注意: JWT是无状态的，实际登出需要在客户端删除token
    """
    return {"message": "登出成功", "user_id": user.id}


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshTokenRequest,
    session: Session = Depends(get_db_session)
) -> TokenResponse:
    """
    刷新访问token
    
    使用refresh_token获取新的access_token
    """
    # TODO: 实现refresh_token验证和刷新逻辑
    # 这里需要一个专门的refresh token机制
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="刷新token功能尚未实现"
    )

