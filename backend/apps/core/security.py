"""Security helpers for JWT tokens and password hashing."""
from datetime import datetime, timedelta
from typing import Any, Dict, List

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""

    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plaintext password."""

    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    roles: List[str],
    user_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token with role claims."""

    settings = get_settings()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode: Dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "roles": roles,
        "uid": user_id,
    }
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token, returning its payload."""

    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:  # pragma: no cover - JWT failure
        raise ValueError("Invalid token") from exc
