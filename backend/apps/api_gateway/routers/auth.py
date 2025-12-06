"""Authentication routes with role-aware JWT tokens."""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_current_user, get_db_session
from apps.core.models import User, UserPreference, UserProfile
from apps.core.security import create_access_token, verify_password, get_password_hash

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    """Token plus user info response."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    roles: list[str] = []
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    """Login payload placeholder."""
    username: str
    password: str
    remember: bool = False


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    student_id: str = Field(..., min_length=5, max_length=20)
    password: str = Field(..., min_length=6)
    confirm_password: str


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_db_session)) -> TokenResponse:
    """Issue an access token after validating credentials against the DB."""

    # ✅ 支持用户名或邮箱登录
    user = session.execute(
        select(User).where(
            (User.username == payload.username) | (User.email == payload.username)
        )
    ).scalar_one_or_none()
    
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    # 安全获取角色
    try:
        roles = [role.name for role in user.roles]
    except Exception:
        roles = []
    
    # 如果选择"记住我"，延长token有效期
    expires_delta = timedelta(days=7) if payload.remember else timedelta(minutes=60)
    
    token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "roles": roles},
        expires_delta=expires_delta,
    )

    # 安全获取 display_name
    display_name = None
    try:
        if user.profile:
            display_name = user.profile.display_name
    except Exception:
        pass

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        roles=roles,
        display_name=display_name,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    session: Session = Depends(get_db_session)
) -> TokenResponse:
    """Register a new user and return JWT tokens."""
    
    # 验证密码
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

    # 检查学号是否已存在
    existing_student = session.execute(
        select(User).where(User.student_id == payload.student_id)
    ).scalar_one_or_none()
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学号已被注册"
        )

    # 创建新用户
    new_user = User(
        username=payload.username,
        email=payload.email,
        student_id=payload.student_id,
        hashed_password=get_password_hash(payload.password),
    )
    
    session.add(new_user)
    session.flush()  # ✅ 使用 flush 获取 ID，而不是 commit

    # 在 flush 后获取所需数据
    user_id = new_user.id
    user_email = new_user.email

    # 创建 token
    access_token = create_access_token(
        data={"sub": user_email, "user_id": user_id, "roles": []}
    )

    # ✅ 不要手动调用 session.commit()，让 get_db_session 自动处理
    return TokenResponse(
        access_token=access_token,
        user_id=user_id,
        roles=[],
        display_name=None,
    )


@router.get("/me", response_model=TokenResponse)
def read_me(user: User = Depends(get_current_user)) -> TokenResponse:
    """Return current user profile info and a refreshed token."""

    try:
        roles = [role.name for role in user.roles]
    except Exception:
        roles = []

    token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "roles": roles}
    )

    display_name = None
    try:
        if user.profile:
            display_name = user.profile.display_name
    except Exception:
        pass

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        roles=roles,
        display_name=display_name,
    )


@router.post("/logout")
def logout():
    """用户登出 - JWT是无状态的，客户端删除token即可"""
    return {"message": "登出成功"}


# ==================== 用户资料管理 ====================

class UserProfileUpdateRequest(BaseModel):
    """用户资料更新请求"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=120)
    phone: Optional[str] = Field(None, max_length=32)
    campus: Optional[str] = Field(None, max_length=120)
    bio: Optional[str] = Field(None, max_length=500)


class UserProfileResponse(BaseModel):
    """用户资料响应"""
    user_id: int
    display_name: str
    phone: Optional[str] = None
    campus: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class PrivacySettings(BaseModel):
    """用户隐私设置"""

    show_email: bool = False
    show_phone: bool = False
    allow_follow: bool = True
    allow_message: bool = True


class NotificationSettings(BaseModel):
    """用户通知设置"""

    email_notification: bool = True
    message_notification: bool = True
    transaction_notification: bool = True
    comment_notification: bool = True
    system_notification: bool = True


class UserPreferencesResponse(BaseModel):
    """组合偏好设置响应"""

    privacy: PrivacySettings
    notifications: NotificationSettings


@router.get("/profile", response_model=UserProfileResponse)
def get_user_profile(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """获取用户资料"""
    profile = session.get(UserProfile, current_user.id)
    if not profile:
        # 如果没有资料，创建一个默认的
        profile = UserProfile(
            user_id=current_user.id,
            display_name=current_user.username
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)
    
    return UserProfileResponse(
        user_id=profile.user_id,
        display_name=profile.display_name,
        phone=profile.phone,
        campus=profile.campus,
        bio=profile.bio,
        avatar_url=profile.avatar_url
    )


@router.put("/profile", response_model=UserProfileResponse)
def update_user_profile(
    payload: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """更新用户资料"""
    profile = session.get(UserProfile, current_user.id)
    if not profile:
        profile = UserProfile(
            user_id=current_user.id,
            display_name=current_user.username
        )
        session.add(profile)
    
    # 更新字段
    if payload.display_name is not None:
        profile.display_name = payload.display_name
    if payload.phone is not None:
        profile.phone = payload.phone
    if payload.campus is not None:
        profile.campus = payload.campus
    if payload.bio is not None:
        profile.bio = payload.bio
    
    session.commit()
    session.refresh(profile)
    
    return UserProfileResponse(
        user_id=profile.user_id,
        display_name=profile.display_name,
        phone=profile.phone,
        campus=profile.campus,
        bio=profile.bio,
        avatar_url=profile.avatar_url
    )


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str = Field(..., min_length=6)


@router.put("/password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """修改密码"""
    # 验证旧密码
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="旧密码错误")
    
    # 更新密码
    current_user.hashed_password = get_password_hash(payload.new_password)
    session.commit()
    
    return {"message": "密码修改成功"}


def _get_or_create_preferences(session: Session, user_id: int) -> UserPreference:
    prefs = session.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    ).scalar_one_or_none()
    if prefs is None:
        prefs = UserPreference(user_id=user_id)
        session.add(prefs)
        session.commit()
        session.refresh(prefs)
    return prefs


def _serialize_privacy(prefs: UserPreference) -> PrivacySettings:
    return PrivacySettings(
        show_email=prefs.show_email,
        show_phone=prefs.show_phone,
        allow_follow=prefs.allow_follow,
        allow_message=prefs.allow_message,
    )


def _serialize_notifications(prefs: UserPreference) -> NotificationSettings:
    return NotificationSettings(
        email_notification=prefs.email_notification,
        message_notification=prefs.message_notification,
        transaction_notification=prefs.transaction_notification,
        comment_notification=prefs.comment_notification,
        system_notification=prefs.system_notification,
    )


@router.get("/preferences", response_model=UserPreferencesResponse)
def get_user_preferences(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    prefs = _get_or_create_preferences(session, current_user.id)
    return UserPreferencesResponse(
        privacy=_serialize_privacy(prefs),
        notifications=_serialize_notifications(prefs),
    )


@router.put("/preferences/privacy", response_model=PrivacySettings)
def update_privacy_settings(
    payload: PrivacySettings,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    prefs = _get_or_create_preferences(session, current_user.id)
    for field, value in payload.model_dump().items():
        setattr(prefs, field, value)
    session.commit()
    session.refresh(prefs)
    return _serialize_privacy(prefs)


@router.put("/preferences/notifications", response_model=NotificationSettings)
def update_notification_settings(
    payload: NotificationSettings,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    prefs = _get_or_create_preferences(session, current_user.id)
    for field, value in payload.model_dump().items():
        setattr(prefs, field, value)
    session.commit()
    session.refresh(prefs)
    return _serialize_notifications(prefs)

