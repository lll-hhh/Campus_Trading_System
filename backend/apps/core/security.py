"""Security utilities for password hashing and JWT tokens."""
from datetime import datetime, timedelta
from typing import Optional, Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from apps.core.config import get_settings

settings = get_settings()

# 密码哈希
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})

    # ✅ 修复：使用 jwt_secret_key 和 jwt_algorithm
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,  # 👈 改成 jwt_secret_key
        algorithm=settings.jwt_algorithm,  # 👈 改成 jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,  # 👈 改成 jwt_secret_key
            algorithms=[settings.jwt_algorithm],  # 👈 改成 jwt_algorithm
        )
        return payload
    except JWTError:
        return None