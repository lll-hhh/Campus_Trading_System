"""API Gateway 依赖注入模块
提供数据库会话、用户认证等依赖
"""
from typing import Callable, Generator, Iterable, Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from jose import JWTError

from apps.core.config import Settings, get_settings
from apps.core.database import db_manager
from apps.core.models import User
from apps.core.security import decode_access_token

# OAuth2 认证 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话
    使用 MySQL 作为主数据库
    """
    with db_manager.session_scope("mysql") as session:
        yield session


def get_current_settings() -> Settings:
    """获取应用配置"""
    return get_settings()


def get_current_token(token: str = Depends(oauth2_scheme)) -> str:
    """获取当前 JWT Token"""
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db_session)
) -> User:
    """
    获取当前登录用户
    从 JWT Token 中解析并返回用户对象
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_access_token(token)
        if payload is None:
            raise credentials_exception
        
        # 尝试从 payload 中获取用户标识
        user_id = payload.get("user_id")
        email = payload.get("sub")
        
        if user_id:
            user = session.get(User, int(user_id))
        elif email:
            user = session.execute(
                select(User).where(User.email == email)
            ).scalar_one_or_none()
        else:
            raise credentials_exception
            
    except (JWTError, ValueError):
        raise credentials_exception
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_db_session)
) -> Optional[User]:
    """
    获取当前用户（可选）
    如果没有提供 token 或 token 无效，返回 None 而不是抛出异常
    """
    if not authorization:
        return None
    
    try:
        # 提取 Bearer token
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            return None
        
        # 验证 token
        payload = decode_access_token(token)
        if payload is None:
            return None
        
        # 尝试从 payload 中获取用户标识
        user_id = payload.get("user_id")
        email = payload.get("sub")
        
        if user_id:
            user = session.get(User, int(user_id))
        elif email:
            user = session.execute(
                select(User).where(User.email == email)
            ).scalar_one_or_none()
        else:
            return None
        
        return user
        
    except (JWTError, ValueError):
        return None


def require_roles(*roles: str) -> Callable[[User], User]:
    """
    生成一个依赖，确保当前用户拥有至少一个所需角色
    """
    def dependency(user: User = Depends(get_current_user)) -> User:
        if not roles:
            return user
        user_roles = {role.name for role in user.roles}
        required: Iterable[str] = set(roles)
        if user_roles.intersection(required):
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )

    return dependency


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前管理员用户"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user
